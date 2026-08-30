"""
Neutral 3D Head Pose Ellipsoid Calibrator.
Fits the multivariate Gaussian neutral head orientation ellipsoid E_head = (mu_head, Sigma_head^-1)
to compute Mahalanobis pose confidence metrics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple
import numpy as np


@dataclass(frozen=True)
class HeadPoseCalibrationResult:
    """Computed neutral head pose ellipsoid parameters."""
    mean_euler_angles: Tuple[float, float, float]
    covariance_matrix_3x3: Tuple[Tuple[float, ...], ...]
    precision_matrix_3x3: Tuple[Tuple[float, ...], ...]
    is_positive_definite: bool
    sample_count: int


class HeadPoseCalibrator:
    """
    Computes empirical neutral head orientation distribution parameters.
    Regularizes sample covariance to guarantee numerical invertibility.
    """

    def __init__(self, ridge_epsilon: float = 1e-3) -> None:
        self.ridge_epsilon = float(ridge_epsilon)

    def fit(
        self,
        euler_samples: Sequence[Tuple[float, float, float]]
    ) -> HeadPoseCalibrationResult:
        """
        Fits 3D mean and regularized inverse covariance from neutral head pose samples.

        Args:
            euler_samples: List of (yaw, pitch, roll) angles in degrees.

        Returns:
            HeadPoseCalibrationResult containing mean and precision matrices.
        """
        if len(euler_samples) < 10:
            raise ValueError(f"Head pose calibration requires at least 10 samples, got {len(euler_samples)}")

        X = np.asarray(euler_samples, dtype=np.float64) # shape (N, 3)
        n_samples = X.shape[0]

        # 1. Compute empirical mean vector
        mean_vec = np.mean(X, axis=0) # shape (3,)

        # 2. Compute sample covariance with Tikhonov ridge regularization
        diff = X - mean_vec
        sample_cov = np.dot(diff.T, diff) / float(max(1, n_samples - 1))
        reg_cov = sample_cov + self.ridge_epsilon * np.eye(3, dtype=np.float64)

        # 3. Check positive-definiteness & compute inverse (precision matrix)
        try:
            # Cholesky decomposition tests positive-definiteness
            L = np.linalg.cholesky(reg_cov)
            cov_inv = np.linalg.inv(reg_cov)
            is_pos_def = True
        except np.linalg.LinAlgError:
            # Fallback to pseudo-inverse with strong diagonal damping
            cov_inv = np.linalg.pinv(reg_cov + 0.01 * np.eye(3, dtype=np.float64))
            is_pos_def = False

        mean_tuple = (float(mean_vec[0]), float(mean_vec[1]), float(mean_vec[2]))
        cov_tuple = tuple(tuple(float(v) for v in row) for row in reg_cov)
        inv_tuple = tuple(tuple(float(v) for v in row) for row in cov_inv)

        return HeadPoseCalibrationResult(
            mean_euler_angles=mean_tuple,
            covariance_matrix_3x3=cov_tuple,
            precision_matrix_3x3=inv_tuple,
            is_positive_definite=is_pos_def,
            sample_count=n_samples
        )


__all__ = ["HeadPoseCalibrator", "HeadPoseCalibrationResult"]
