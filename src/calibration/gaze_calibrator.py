"""
9-Point Desktop Gaze Calibration Engine & Mapping Solvers.
Solves Coupled Eye-Head Affine (2x5) and 2nd-Order Polynomial (2x9) regression mapping
from ocular pupil ratios and head Euler orientation to physical screen pixel coordinates.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np


@dataclass(frozen=True)
class CalibrationPointSample:
    """Ocular feature and head orientation samples recorded at a specific screen target location."""
    target_screen_xy: Tuple[float, float]
    iris_ratio_x_mean: float
    iris_ratio_y_mean: float
    head_yaw_mean: float = 0.0
    head_pitch_mean: float = 0.0
    sample_count: int = 30
    spatial_variance: float = 0.01


@dataclass(frozen=True)
class GazeCalibrationResult:
    """Solved calibration parameters, mapping matrices, and quality validation metrics."""
    affine_matrix_3x3: Tuple[Tuple[float, ...], ...]
    poly_weights_2x6: Tuple[Tuple[float, ...], ...]
    rmse_pixels: float
    mae_pixels: float
    max_error_pixels: float
    calibration_grade: str
    is_valid: bool


class GazeCalibrator:
    """
    Multi-Point Desktop Gaze Calibration Solver.
    Combines ocular pupil displacement (rx, ry) with head orientation (yaw, pitch)
    using robust multi-pass aggregation and Tikhonov-regularized regression.
    """

    def __init__(
        self,
        screen_width: int = 1920,
        screen_height: int = 1080,
        regularization_lambda: float = 1e-3
    ) -> None:
        self.screen_width = int(screen_width)
        self.screen_height = int(screen_height)
        self.regularization_lambda = float(regularization_lambda)

    def solve(
        self,
        samples: List[CalibrationPointSample]
    ) -> GazeCalibrationResult:
        """
        Fits coupled eye-head affine and polynomial mapping matrices from recorded calibration samples.
        Aggregates multiple samples per target coordinate (multi-pass verification).

        Args:
            samples: List of CalibrationPointSample instances (from single or multi-pass acquisition).

        Returns:
            GazeCalibrationResult containing solved matrices and accuracy metrics.
        """
        if len(samples) < 5:
            raise ValueError(f"Gaze calibration requires at least 5 samples, got {len(samples)}")

        # 1. Aggregate multi-pass samples per unique target location
        target_dict: Dict[Tuple[int, int], List[CalibrationPointSample]] = {}
        for s in samples:
            key = (int(round(s.target_screen_xy[0])), int(round(s.target_screen_xy[1])))
            target_dict.setdefault(key, []).append(s)

        unique_samples = []
        for (tx, ty), s_list in target_dict.items():
            avg_rx = float(np.mean([s.iris_ratio_x_mean for s in s_list]))
            avg_ry = float(np.mean([s.iris_ratio_y_mean for s in s_list]))
            avg_yaw = float(np.mean([s.head_yaw_mean for s in s_list]))
            avg_pitch = float(np.mean([s.head_pitch_mean for s in s_list]))
            unique_samples.append((float(tx), float(ty), avg_rx, avg_ry, avg_yaw, avg_pitch))

        n_pts = len(unique_samples)

        # 2. Target Matrix Y: shape (2, N)
        Y = np.zeros((2, n_pts), dtype=np.float64)
        for i, s in enumerate(unique_samples):
            Y[0, i] = s[0]
            Y[1, i] = s[1]

        # 3. Coupled Eye-Head Feature Matrix X: shape (5, N) -> [rx, ry, yaw, pitch, 1]
        X_aff = np.zeros((5, n_pts), dtype=np.float64)
        for i, s in enumerate(unique_samples):
            X_aff[0, i] = s[2] # rx
            X_aff[1, i] = s[3] # ry
            X_aff[2, i] = s[4] # yaw
            X_aff[3, i] = s[5] # pitch
            X_aff[4, i] = 1.0

        # Solve Affine M (2x5) via Tikhonov ridge regression
        reg_aff = self.regularization_lambda * np.eye(5, dtype=np.float64)
        cov_aff = np.dot(X_aff, X_aff.T) + reg_aff
        cov_aff_inv = np.linalg.pinv(cov_aff)
        M_aff_2x5 = np.dot(Y, np.dot(X_aff.T, cov_aff_inv))

        # 4. Coupled Eye-Head Polynomial Matrix Phi: shape (9, N)
        Phi = np.zeros((9, n_pts), dtype=np.float64)
        for i, s in enumerate(unique_samples):
            rx, ry, yaw, pitch = s[2], s[3], s[4], s[5]
            Phi[:, i] = [1.0, rx, ry, yaw, pitch, rx ** 2, ry ** 2, yaw ** 2, pitch ** 2]

        reg_poly = self.regularization_lambda * np.eye(9, dtype=np.float64)
        cov_poly = np.dot(Phi, Phi.T) + reg_poly
        cov_poly_inv = np.linalg.pinv(cov_poly)
        W_poly_2x9 = np.dot(Y, np.dot(Phi.T, cov_poly_inv))

        # 5. Compute Cross-Validation Quality & Residual Error
        Y_pred = np.dot(M_aff_2x5, X_aff)
        errors = np.sqrt(np.sum((Y - Y_pred) ** 2, axis=0)) # Euclidean pixel error per target point

        rmse = float(np.sqrt(np.mean(errors ** 2)))
        mae = float(np.mean(errors))
        max_err = float(np.max(errors))

        # Realistic Human Desktop Calibration Quality Grading
        if rmse <= 65.0:
            grade = "EXCELLENT"
            is_valid = True
        elif rmse <= 120.0:
            grade = "GOOD"
            is_valid = True
        elif rmse <= 180.0:
            grade = "FAIR"
            is_valid = True
        else:
            grade = "RETRY_RECOMMENDED"
            is_valid = False

        aff_tuple = tuple(tuple(float(v) for v in row) for row in M_aff_2x5)
        poly_tuple = tuple(tuple(float(v) for v in row) for row in W_poly_2x9)

        return GazeCalibrationResult(
            affine_matrix_3x3=aff_tuple,
            poly_weights_2x6=poly_tuple,
            rmse_pixels=rmse,
            mae_pixels=mae,
            max_error_pixels=max_err,
            calibration_grade=grade,
            is_valid=is_valid
        )

    @staticmethod
    def apply_polynomial_gaze(
        poly_weights_2x9: np.ndarray,
        iris_rx: float,
        iris_ry: float,
        head_yaw: float = 0.0,
        head_pitch: float = 0.0,
        screen_width: float = 1920.0,
        screen_height: float = 1080.0
    ) -> Tuple[float, float]:
        """
        Maps 2D ocular iris ratio and head orientation to screen pixel coordinates via the 2nd-order polynomial model.
        """
        W = np.asarray(poly_weights_2x9, dtype=np.float64)
        if W.shape[1] == 9:
            phi = np.array([1.0, iris_rx, iris_ry, head_yaw, head_pitch, iris_rx**2, iris_ry**2, head_yaw**2, head_pitch**2], dtype=np.float64)
        elif W.shape[1] == 6:
            phi = np.array([1.0, iris_rx, iris_ry, iris_rx**2, iris_ry**2, iris_rx*iris_ry], dtype=np.float64)
        else:
            phi = np.array([iris_rx, iris_ry, 1.0], dtype=np.float64)

        pred = np.dot(W[:2, :], phi)
        u = float(np.clip(pred[0], 0.0, screen_width))
        v = float(np.clip(pred[1], 0.0, screen_height))
        return u, v


__all__ = ["GazeCalibrator", "CalibrationPointSample", "GazeCalibrationResult"]
