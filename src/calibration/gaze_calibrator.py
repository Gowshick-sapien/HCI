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

        # 3. Decoupled Orthogonal Regression to eliminate horizontal-vertical cross-talk:
        # Screen X depends strictly on [rx, yaw, 1.0]
        # Screen Y depends strictly on [ry, pitch, 1.0]
        tx = Y[0, :]
        ty = Y[1, :]
        rx = np.array([s[2] for s in unique_samples], dtype=np.float64)
        ry = np.array([s[3] for s in unique_samples], dtype=np.float64)
        yaw = np.array([s[4] for s in unique_samples], dtype=np.float64)
        pitch = np.array([s[5] for s in unique_samples], dtype=np.float64)

        def solve_axis_ridge(
            targets: np.ndarray,
            feat_ocular: np.ndarray,
            feat_head: np.ndarray,
            reg: float = 1e-3
        ) -> Tuple[float, float, float]:
            f1_c = feat_ocular - np.mean(feat_ocular)
            f2_c = feat_head - np.mean(feat_head)
            t_c = targets - np.mean(targets)
            s1 = float(np.std(feat_ocular)) if float(np.std(feat_ocular)) > 1e-6 else 1.0
            s2 = float(np.std(feat_head)) if float(np.std(feat_head)) > 1e-6 else 1.0

            Z = np.vstack([f1_c / s1, f2_c / s2])
            cov = np.dot(Z, Z.T) + reg * np.eye(2, dtype=np.float64)
            w_std = np.dot(t_c, np.dot(Z.T, np.linalg.pinv(cov)))

            w_ocular = float(w_std[0] / s1)
            w_head = float(w_std[1] / s2)
            bias = float(np.mean(targets) - w_ocular * np.mean(feat_ocular) - w_head * np.mean(feat_head))
            return w_ocular, w_head, bias

        w_rx, w_yaw, b_x = solve_axis_ridge(tx, rx, yaw, self.regularization_lambda)
        w_ry, w_pitch, b_y = solve_axis_ridge(ty, ry, pitch, self.regularization_lambda)

        # Assemble decoupled 2x5 Affine Matrix
        # [ [w_rx, 0.0,  w_yaw, 0.0,     b_x],
        #   [0.0,  w_ry, 0.0,   w_pitch, b_y] ]
        M_aff_2x5 = np.array([
            [w_rx, 0.0, w_yaw, 0.0, b_x],
            [0.0, w_ry, 0.0, w_pitch, b_y]
        ], dtype=np.float64)

        # 4. Decoupled Polynomial Matrix: shape (2, 9)
        # Phi slots: [1.0, rx, ry, yaw, pitch, rx**2, ry**2, yaw**2, pitch**2]
        # For X: solve [1.0, rx, yaw, rx**2, yaw**2] -> slots 0, 1, 3, 5, 7
        # For Y: solve [1.0, ry, pitch, ry**2, pitch**2] -> slots 0, 2, 4, 6, 8
        Phi_x = np.vstack([np.ones(n_pts, dtype=np.float64), rx, yaw, rx**2, yaw**2])
        cov_px = np.dot(Phi_x, Phi_x.T) + self.regularization_lambda * np.eye(5, dtype=np.float64)
        w_px = np.dot(tx, np.dot(Phi_x.T, np.linalg.pinv(cov_px)))

        Phi_y = np.vstack([np.ones(n_pts, dtype=np.float64), ry, pitch, ry**2, pitch**2])
        cov_py = np.dot(Phi_y, Phi_y.T) + self.regularization_lambda * np.eye(5, dtype=np.float64)
        w_py = np.dot(ty, np.dot(Phi_y.T, np.linalg.pinv(cov_py)))

        W_poly_2x9 = np.zeros((2, 9), dtype=np.float64)
        W_poly_2x9[0, [0, 1, 3, 5, 7]] = w_px
        W_poly_2x9[1, [0, 2, 4, 6, 8]] = w_py

        # 5. Compute Cross-Validation Quality & Residual Error
        X_aff_full = np.vstack([rx, ry, yaw, pitch, np.ones(n_pts, dtype=np.float64)])
        Y_pred = np.dot(M_aff_2x5, X_aff_full)
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
