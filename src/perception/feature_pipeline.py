"""
Layer 1 Perception Feature Pipeline Coordinator.
Assembles raw video frames into the unified, strongly-typed PerceptionFrame schema.
Orchestrates FaceMesh, SolvePnP 3D Head Pose, MediaPipe Hands, 1-Euro Filter,
and Gaze Dwell Tracker.
"""

from __future__ import annotations

import logging
import time
from typing import Optional, Tuple
import cv2
import numpy as np

from src.capture.frame_types import RawFrame
from src.perception.face_mesh_extractor import FaceMeshExtractor
from src.perception.gaze_dwell_tracker import GazeDwellTracker
from src.perception.hand_pose_extractor import HandPoseExtractor
from src.perception.head_pose_estimator import HeadPoseEstimator
from src.perception.one_euro_filter import OneEuroFilter
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

    HEAD_YAW_RANGE: float = 30.0    # Angular range (deg) for full horizontal screen extent
    HEAD_PITCH_RANGE: float = 25.0  # Angular range (deg) for full vertical screen extent
    EYE_GAIN_X: float = 300.0       # Eye vernier horizontal gain (px)
    EYE_GAIN_Y: float = 300.0       # Eye vernier vertical gain (px)
    MAX_EYE_DELTA: float = 150.0    # Clamped eye vernier radius (px)

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
            ear_blink_threshold=ear_blink_threshold,
        )
        self.head_pose_estimator = HeadPoseEstimator(camera_fov_degrees=self.camera_fov_degrees)
        self.hand_pose_extractor = HandPoseExtractor(
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        # 2. Adaptive temporal filtering on composite screen gaze output
        self.one_euro_filter = OneEuroFilter(fc_min=0.8, beta=0.007, d_cutoff=1.0, dim=2)

        # 3. Gaze Fixation & Dwell Tracker
        self.gaze_dwell_tracker = GazeDwellTracker(
            fixation_radius_px=fixation_radius_px,
            default_tau_dwell_ms=default_tau_dwell_ms,
        )

    def process_frame(
        self,
        raw_frame: RawFrame,
        profile: Optional[ProfileSnapshot] = None,
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
            neutral_cov_inv=neutral_cov_inv,
        )

        # 3. 3D Hand Kinematics Extraction
        hand_data = self.hand_pose_extractor.extract(img, timestamp_sec=raw_frame.timestamp)

        # 4. Head pose telemetry
        if head_data is not None:
            head_euler = (float(head_data.yaw), float(head_data.pitch), float(head_data.roll))
            head_conf = float(head_data.confidence)
        else:
            head_euler = (0.0, 0.0, 0.0)
            head_conf = 0.0
            head_data = HeadPoseLandmarks(
                yaw=0.0,
                pitch=0.0,
                roll=0.0,
                translation_vector=(0.0, 0.0, 0.0),
                mahalanobis_distance=0.0,
                confidence=0.0,
                variance=0.50,
            )

        # 5. Dual-Stage Composite Gaze Pipeline (Face Carrier + Eye Vernier) with 1-Euro Filtering
        calibrated = bool(
            profile
            and profile.gaze_calibration_matrix
            and profile.last_recalibration_timestamp > 0
            and getattr(profile, "gaze_feature_version", 1) >= 4
            and np.asarray(profile.gaze_calibration_matrix).shape in ((2, 5), (3, 5))
        )

        has_face = (head_conf > 0.0) or (eye_data is not None and eye_data.confidence > 0.0)

        if calibrated and eye_data is not None and eye_data.confidence > 0.0:
            M_gaze = np.asarray(profile.gaze_calibration_matrix, dtype=np.float64)
            raw_screen_u, raw_screen_v = apply_affine_gaze(
                M_gaze,
                eye_data.iris_ratio_x,
                eye_data.iris_ratio_y,
                head_yaw=head_euler[0],
                head_pitch=head_euler[1],
            )
            raw_u = float(np.clip(raw_screen_u, 0.0, self.screen_width))
            raw_v = float(np.clip(raw_screen_v, 0.0, self.screen_height))
            filtered = self.one_euro_filter.update([raw_u, raw_v], timestamp_sec=raw_frame.timestamp)
            gaze_screen_xy = (float(filtered[0]), float(filtered[1]))
            gaze_conf = float(eye_data.confidence)
            ear_val = float((eye_data.left_ear + eye_data.right_ear) / 2.0)
        elif has_face:
            # Uncalibrated fallback: Dual-Stage Composite Gaze (Face Carrier + Eye Vernier)
            neutral_yaw = 0.0
            neutral_pitch = 0.0
            if profile and profile.neutral_pose_mean and len(profile.neutral_pose_mean) >= 2:
                neutral_yaw = float(profile.neutral_pose_mean[0])
                neutral_pitch = float(profile.neutral_pose_mean[1])

            delta_yaw = head_euler[0] - neutral_yaw
            delta_pitch = head_euler[1] - neutral_pitch

            # Stage 1 -- Face Carrier (coarse position, SNR >60:1)
            face_u = self.screen_width * (0.50 + delta_yaw / self.HEAD_YAW_RANGE)
            face_v = self.screen_height * (0.50 + delta_pitch / self.HEAD_PITCH_RANGE)

            # Stage 2 -- Eye Vernier (localized fine adjustment, clamped radius)
            rx = eye_data.iris_ratio_x if eye_data is not None else 0.50
            ry = eye_data.iris_ratio_y if eye_data is not None else 0.50
            eye_delta_u = -self.EYE_GAIN_X * (rx - 0.50)
            eye_delta_v = self.EYE_GAIN_Y * (ry - 0.50)
            eye_delta_u = float(np.clip(eye_delta_u, -self.MAX_EYE_DELTA, self.MAX_EYE_DELTA))
            eye_delta_v = float(np.clip(eye_delta_v, -self.MAX_EYE_DELTA, self.MAX_EYE_DELTA))

            # Stage 3 -- Composite Integration + 1-Euro Filtering
            raw_u = float(np.clip(face_u + eye_delta_u, 0.0, self.screen_width))
            raw_v = float(np.clip(face_v + eye_delta_v, 0.0, self.screen_height))
            filtered = self.one_euro_filter.update([raw_u, raw_v], timestamp_sec=raw_frame.timestamp)
            gaze_screen_xy = (float(filtered[0]), float(filtered[1]))
            gaze_conf = 0.35
            ear_val = float((eye_data.left_ear + eye_data.right_ear) / 2.0) if eye_data is not None else 0.0
        else:
            gaze_screen_xy = (self.screen_width / 2.0, self.screen_height / 2.0)
            gaze_conf = 0.0
            ear_val = 0.0

        # 6. Gaze Dwell Tracking
        tau_dwell = profile.gaze_target_dwell_ms if profile else 120.0
        dwell_input = gaze_screen_xy if gaze_conf > 0.0 else None
        dwell_metrics = self.gaze_dwell_tracker.update(dwell_input, timestamp_ms, tau_dwell_ms=tau_dwell)

        # Fallback eye data if None
        if eye_data is None:
            eye_data = EyeLandmarks(
                left_iris_center=(0.0, 0.0),
                right_iris_center=(0.0, 0.0),
                left_ear=0.0,
                right_ear=0.0,
                iris_ratio_x=0.5,
                iris_ratio_y=0.5,
                confidence=0.0,
                variance=0.50,
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
            eye_aspect_ratio=ear_val,
        )

    def _create_empty_perception_frame(self, raw_frame: RawFrame) -> PerceptionFrame:
        """Returns default PerceptionFrame when input image is invalid."""
        self.one_euro_filter.reset()
        eye_data = EyeLandmarks(
            left_iris_center=(0.0, 0.0),
            right_iris_center=(0.0, 0.0),
            left_ear=0.0,
            right_ear=0.0,
            iris_ratio_x=0.5,
            iris_ratio_y=0.5,
            confidence=0.0,
            variance=0.50,
        )
        head_data = HeadPoseLandmarks(
            yaw=0.0,
            pitch=0.0,
            roll=0.0,
            translation_vector=(0.0, 0.0, 0.0),
            mahalanobis_distance=0.0,
            confidence=0.0,
            variance=0.50,
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
            eye_aspect_ratio=0.28,
        )

    def close(self) -> None:
        """Releases underlying computer vision models."""
        self.face_mesh_extractor.close()
        self.hand_pose_extractor.close()
        self.one_euro_filter.reset()


__all__ = ["FeaturePipeline"]
