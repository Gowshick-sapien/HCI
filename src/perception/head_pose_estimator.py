"""
Head Pose 3D Estimator.
Uses Levenberg-Marquardt SolvePnP on 6 canonical facial anthropometric landmarks
to compute 3D Euler orientation angles (yaw, pitch, roll) and pose confidence.
"""

from __future__ import annotations

from typing import List, Optional, Tuple
import cv2
import numpy as np

from src.storage.schemas import HeadPoseLandmarks
from src.utils.geometry import compute_mahalanobis_distance


class HeadPoseEstimator:
    """
    3D Head Pose Estimator based on cv2.solvePnP with Levenberg-Marquardt optimization.
    Standard camera coordinate frame: +X right, +Y down, +Z forward.
    """

    # 6 Canonical facial feature landmark indices
    NOSE_TIP = 1
    CHIN = 199
    LEFT_EYE_OUTER = 33
    RIGHT_EYE_OUTER = 263
    LEFT_MOUTH_CORNER = 61
    RIGHT_MOUTH_CORNER = 291

    CANONICAL_INDICES = [NOSE_TIP, CHIN, LEFT_EYE_OUTER, RIGHT_EYE_OUTER, LEFT_MOUTH_CORNER, RIGHT_MOUTH_CORNER]

    # Anthropometric 3D reference model coordinates (+Y is down, +Z is recessed depth)
    MODEL_POINTS_3D = np.array([
        [0.0, 0.0, 0.0],          # Nose tip
        [0.0, 330.0, 65.0],        # Chin
        [-225.0, -170.0, 135.0],   # Left eye outer corner
        [225.0, -170.0, 135.0],    # Right eye outer corner
        [-150.0, 150.0, 125.0],    # Left mouth corner
        [150.0, 150.0, 125.0]      # Right mouth corner
    ], dtype=np.float64)

    def __init__(self, camera_fov_degrees: float = 60.0) -> None:
        self.camera_fov_degrees = float(camera_fov_degrees)
        self._dist_coeffs = np.zeros((4, 1), dtype=np.float64)

    def estimate(
        self,
        landmarks_468: Optional[List[Tuple[float, float, float]]],
        frame_width: int,
        frame_height: int,
        neutral_mean: Optional[np.ndarray] = None,
        neutral_cov_inv: Optional[np.ndarray] = None
    ) -> Optional[HeadPoseLandmarks]:
        """
        Estimates 3D head pose Euler angles and translation vector from 2D facial landmark projections.
        """
        if landmarks_468 is None or len(landmarks_468) < 468:
            return None

        # 1. Extract 2D image points for canonical indices
        image_points = np.array([
            [landmarks_468[idx][0], landmarks_468[idx][1]] for idx in self.CANONICAL_INDICES
        ], dtype=np.float64)

        # 2. Build camera intrinsic matrix from FOV
        focal_length = frame_width / (2.0 * np.tan(np.radians(self.camera_fov_degrees) / 2.0))
        center_x = frame_width / 2.0
        center_y = frame_height / 2.0
        camera_matrix = np.array([
            [focal_length, 0.0, center_x],
            [0.0, focal_length, center_y],
            [0.0, 0.0, 1.0]
        ], dtype=np.float64)

        # 3. Solve PnP with iterative Levenberg-Marquardt
        success, rvec, tvec = cv2.solvePnP(
            self.MODEL_POINTS_3D,
            image_points,
            camera_matrix,
            self._dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE
        )

        if not success:
            return None

        # 4. Convert rotation vector to 3x3 rotation matrix, then Euler angles via RQDecomp3x3
        rmat, _ = cv2.Rodrigues(rvec)
        angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)
        pitch = float(angles[0])
        yaw = float(angles[1])
        roll = float(angles[2])

        # Clipping sanity
        yaw = float(np.clip(yaw, -90.0, 90.0))
        pitch = float(np.clip(pitch, -90.0, 90.0))
        roll = float(np.clip(roll, -90.0, 90.0))

        # 5. Compute Mahalanobis confidence relative to neutral pose
        mean = neutral_mean if neutral_mean is not None else np.array([0.0, 0.0, 0.0], dtype=np.float64)
        cov_inv = neutral_cov_inv if neutral_cov_inv is not None else np.eye(3, dtype=np.float64) * 0.01

        current_pose = (yaw, pitch, roll)
        d_mahalanobis = compute_mahalanobis_distance(current_pose, mean, cov_inv)
        confidence = float(np.exp(-0.5 * min(15.0, d_mahalanobis ** 2)))

        t_vec_tuple = (float(tvec[0, 0]), float(tvec[1, 0]), float(tvec[2, 0]))

        return HeadPoseLandmarks(
            yaw=yaw,
            pitch=pitch,
            roll=roll,
            translation_vector=t_vec_tuple,
            mahalanobis_distance=d_mahalanobis,
            confidence=confidence,
            variance=0.04
        )


__all__ = ["HeadPoseEstimator"]
