"""
Layer 1 Perception Feature Pipeline Coordinator.
Assembles raw video frames into the unified, strongly-typed PerceptionFrame schema.
Orchestrates FaceMesh, SolvePnP 3D Head Pose, MediaPipe Hands, Holt-Winters filters,
and Gaze Dwell Tracker.
"""

from __future__ import annotations

import logging
import math
import time
from typing import Optional, Tuple
import cv2
import numpy as np

from src.capture.frame_types import RawFrame
from src.perception.face_mesh_extractor import FaceMeshExtractor
from src.perception.gaze_dwell_tracker import GazeDwellTracker
from src.perception.hand_pose_extractor import HandPoseExtractor
from src.perception.head_pose_estimator import HeadPoseEstimator
from src.perception.holt_winters_filter import HoltWintersFilter
from src.storage.schemas import (
    EyeLandmarks,
    HeadPoseLandmarks,
    PerceptionFrame,
    ProfileSnapshot,
)
from src.utils.geometry import apply_affine_gaze

logger = logging.getLogger(__name__)


class FeaturePipeline:
    """
    Unified multimodal feature extraction coordinator for Layer 1.
    Processes RawFrame instances within a <= 20.5 ms latency budget on CPU.
    """

    def __init__(
        self,
        camera_fov_degrees: float = 60.0,
        screen_width: int = 1920,
        screen_height: int = 1080,
        ear_blink_threshold: float = 0.18,
        fixation_radius_px: float = 85.0,
        default_tau_dwell_ms: float = 120.0,
    ) -> None:
        self.camera_fov_degrees = float(camera_fov_degrees)
        self.screen_width = int(screen_width)
        self.screen_height = int(screen_height)

        # 1. Computer Vision Feature Extractors
        self.face_mesh_extractor = FaceMeshExtractor(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            ear_blink_threshold=ear_blink_threshold
        )
        self.head_pose_estimator = HeadPoseEstimator(camera_fov_degrees=self.camera_fov_degrees)
        self.hand_pose_extractor = HandPoseExtractor(
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # 2. Dynamic Spatial Smoothing Filters
        # Ocular iris ratio filter: eliminates webcam CMOS sensor jitter at the source
        self.iris_filter = HoltWintersFilter(
            dim=2,
            alpha_0=0.15,
            beta=0.0,
            gamma=1.2,
            alpha_min=0.08,
            alpha_max=0.75
        )
        # Spatial screen gaze filter: rock-solid at rest (alpha=0.08), snaps on saccades
        self.gaze_filter = HoltWintersFilter(
            dim=2,
            alpha_0=0.15,
            beta=0.0,
            gamma=0.0035,
            alpha_min=0.08,
            alpha_max=0.85
        )
        self.head_filter = HoltWintersFilter(
            dim=3,
            alpha_0=0.20,
            beta=0.02,
            gamma=0.008,
            alpha_min=0.10,
            alpha_max=0.75
        )
        self._last_locked_gaze: Optional[Tuple[float, float]] = None
        self._deadband_radius_px: float = 14.0

        # 3. Gaze Fixation & Dwell Tracker
        self.gaze_dwell_tracker = GazeDwellTracker(
            fixation_radius_px=fixation_radius_px,
            default_tau_dwell_ms=default_tau_dwell_ms
        )

    def process_frame(
        self,
        raw_frame: RawFrame,
        profile: Optional[ProfileSnapshot] = None
    ) -> PerceptionFrame:
        """
        Executes end-to-end Layer 1 feature extraction and returns an immutable PerceptionFrame.
        """
        t_start = time.perf_counter()
        img = raw_frame.image

        if img is None:
            return self._create_empty_perception_frame(raw_frame)

        h, w = img.shape[:2]
        timestamp_ms = raw_frame.timestamp * 1000.0

        # 1. FaceMesh & Refined Iris Extraction
        eye_data, raw_468 = self.face_mesh_extractor.extract(img)

        # 2. 3D Head Pose Estimation
        neutral_mean = np.array(profile.neutral_pose_mean, dtype=np.float64) if profile else None
        neutral_cov_inv = np.array(profile.neutral_pose_cov_inv, dtype=np.float64) if profile else None
        head_data = self.head_pose_estimator.estimate(
            landmarks_468=raw_468,
            frame_width=w,
            frame_height=h,
            neutral_mean=neutral_mean,
            neutral_cov_inv=neutral_cov_inv
        )

        # 3. 3D Hand Kinematics Extraction
        hand_data = self.hand_pose_extractor.extract(img, timestamp_sec=raw_frame.timestamp)

        # 4. Smooth Head Pose Euler angles first so head coordinates are clean for gaze coupling
        if head_data is not None:
            smoothed_head = self.head_filter.update([head_data.yaw, head_data.pitch, head_data.roll])
            head_euler = (float(smoothed_head[0]), float(smoothed_head[1]), float(smoothed_head[2]))
            head_conf = head_data.confidence
            head_yaw = head_euler[0]
            head_pitch = head_euler[1]
        else:
            head_euler = (0.0, 0.0, 0.0)
            head_conf = 0.0
            head_yaw = 0.0
            head_pitch = 0.0
            head_data = HeadPoseLandmarks(
                yaw=0.0, pitch=0.0, roll=0.0,
                translation_vector=(0.0, 0.0, 0.0),
                mahalanobis_distance=0.0,
                confidence=0.0, variance=0.50
            )

        # 5. Gaze Coordinate Mapping & Spatial Smoothing
        if eye_data is not None and eye_data.confidence > 0.0:
            # Low-pass filter raw iris coordinates to eliminate camera sensor CMOS jitter
            smooth_iris = self.iris_filter.update([eye_data.iris_ratio_x, eye_data.iris_ratio_y])
            iris_rx = float(smooth_iris[0])
            iris_ry = float(smooth_iris[1])

            if profile and profile.gaze_calibration_matrix and profile.last_recalibration_timestamp > 0:
                M_gaze = np.array(profile.gaze_calibration_matrix, dtype=np.float64)
                raw_screen_u, raw_screen_v = apply_affine_gaze(
                    M_gaze,
                    iris_rx,
                    iris_ry,
                    head_yaw=head_yaw,
                    head_pitch=head_pitch
                )
            else:
                # Offset head angles relative to calibrated neutral pose if available
                eff_yaw = head_yaw
                eff_pitch = head_pitch
                if profile and profile.neutral_pose_mean and len(profile.neutral_pose_mean) >= 2:
                    eff_yaw -= profile.neutral_pose_mean[0]
                    eff_pitch -= profile.neutral_pose_mean[1]

                # High-dynamic range baseline gaze mapping with Eye-Head coordination
                norm_gaze_x = (0.50 - iris_rx) * 4.5 + 0.50
                norm_gaze_y = (iris_ry - 0.45) * 4.0 + 0.50

                norm_gaze_x += (eff_yaw / 20.0) * 0.45
                norm_gaze_y += (eff_pitch / 18.0) * 0.40

                raw_screen_u = norm_gaze_x * self.screen_width
                raw_screen_v = norm_gaze_y * self.screen_height

            raw_screen_u = float(np.clip(raw_screen_u, 0.0, self.screen_width))
            raw_screen_v = float(np.clip(raw_screen_v, 0.0, self.screen_height))

            # Apply deadband: if displacement from last locked gaze is within micro-tremor radius, damp it
            if self._last_locked_gaze is not None:
                dist = math.hypot(raw_screen_u - self._last_locked_gaze[0], raw_screen_v - self._last_locked_gaze[1])
                if dist < self._deadband_radius_px:
                    # Subtle blend towards locked position to completely cancel resting jitter
                    blend = dist / self._deadband_radius_px
                    raw_screen_u = self._last_locked_gaze[0] * (1.0 - blend) + raw_screen_u * blend
                    raw_screen_v = self._last_locked_gaze[1] * (1.0 - blend) + raw_screen_v * blend
                else:
                    self._last_locked_gaze = (raw_screen_u, raw_screen_v)
            else:
                self._last_locked_gaze = (raw_screen_u, raw_screen_v)

            # Apply Holt-Winters smoothing with intrinsic gaze velocity for instant saccadic snapping
            smoothed_gaze = self.gaze_filter.update([raw_screen_u, raw_screen_v], velocity_magnitude=None)
            gaze_screen_xy = (float(smoothed_gaze[0]), float(smoothed_gaze[1]))
            gaze_conf = eye_data.confidence
            ear_val = (eye_data.left_ear + eye_data.right_ear) / 2.0
        else:
            gaze_screen_xy = (self.screen_width / 2.0, self.screen_height / 2.0)
            gaze_conf = 0.0
            ear_val = 0.0
            self._last_locked_gaze = None

        # 5. Gaze Dwell Tracking
        tau_dwell = profile.gaze_target_dwell_ms if profile else 120.0
        dwell_input = gaze_screen_xy if gaze_conf > 0.0 else None
        dwell_metrics = self.gaze_dwell_tracker.update(dwell_input, timestamp_ms, tau_dwell_ms=tau_dwell)

        # Fallback eye data if None
        if eye_data is None:
            eye_data = EyeLandmarks(
                left_iris_center=(0.0, 0.0),
                right_iris_center=(0.0, 0.0),
                left_ear=0.0, right_ear=0.0,
                iris_ratio_x=0.5, iris_ratio_y=0.5,
                confidence=0.0, variance=0.50
            )

        # Sensor Covariance estimation (2x2)
        var_gaze = eye_data.variance
        cov_matrix = np.array([[var_gaze, 0.0], [0.0, var_gaze]], dtype=np.float64)

        return PerceptionFrame(
            frame_id=raw_frame.frame_id,
            timestamp_ms=timestamp_ms,
            eye=eye_data,
            head=head_data,
            hand=hand_data,
            gaze_confidence=gaze_conf,
            head_confidence=head_conf,
            gaze_screen_xy=gaze_screen_xy,
            head_euler_angles=head_euler,
            gaze_dwell_ms=dwell_metrics.gaze_dwell_ms,
            gaze_stability=dwell_metrics.gaze_stability,
            gaze_anchor=dwell_metrics.gaze_anchor,
            sensor_covariance_matrix=cov_matrix,
            ambient_illuminance_lux=raw_frame.ambient_lux,
            eye_aspect_ratio=ear_val
        )

    def _create_empty_perception_frame(self, raw_frame: RawFrame) -> PerceptionFrame:
        """Returns default PerceptionFrame when input image is invalid."""
        eye_data = EyeLandmarks(
            left_iris_center=(0.0, 0.0), right_iris_center=(0.0, 0.0),
            left_ear=0.0, right_ear=0.0, iris_ratio_x=0.5, iris_ratio_y=0.5,
            confidence=0.0, variance=0.50
        )
        head_data = HeadPoseLandmarks(
            yaw=0.0, pitch=0.0, roll=0.0, translation_vector=(0.0, 0.0, 0.0),
            mahalanobis_distance=0.0, confidence=0.0, variance=0.50
        )
        hand_data = self.hand_pose_extractor._empty_hand_landmarks()

        return PerceptionFrame(
            frame_id=raw_frame.frame_id,
            timestamp_ms=raw_frame.timestamp * 1000.0,
            eye=eye_data,
            head=head_data,
            hand=hand_data,
            gaze_confidence=0.0,
            head_confidence=0.0,
            gaze_screen_xy=(self.screen_width / 2.0, self.screen_height / 2.0),
            head_euler_angles=(0.0, 0.0, 0.0),
            gaze_dwell_ms=0.0,
            gaze_stability=0.0,
            gaze_anchor=None,
            sensor_covariance_matrix=np.array([[0.50, 0.0], [0.0, 0.50]], dtype=np.float64),
            ambient_illuminance_lux=raw_frame.ambient_lux,
            eye_aspect_ratio=0.28
        )

    def close(self) -> None:
        """Releases underlying computer vision models."""
        self.face_mesh_extractor.close()
        self.hand_pose_extractor.close()


__all__ = ["FeaturePipeline"]
