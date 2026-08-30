"""
Unit tests for 9-Point Gaze Calibration Solver.
Verifies Invariant INV-D3.1: Calibration residual RMSE <= 35.0 px.
"""

import numpy as np
import pytest

from src.calibration.gaze_calibrator import (
    CalibrationPointSample,
    GazeCalibrator,
)


def test_gaze_calibrator_synthetic_9_points():
    """Invariant INV-D3.1: Fits eye-head affine and polynomial mapping with RMSE <= 35 px."""
    w, h = 1920, 1080
    calibrator = GazeCalibrator(screen_width=w, screen_height=h)

    # 9 Normalized target points
    target_norm = [
        (0.1, 0.1), (0.5, 0.1), (0.9, 0.1),
        (0.1, 0.5), (0.5, 0.5), (0.9, 0.5),
        (0.1, 0.9), (0.5, 0.9), (0.9, 0.9)
    ]

    # Generate synthetic coupled eye-head features with linear mapping + slight noise
    samples = []
    np.random.seed(42)
    for tx_norm, ty_norm in target_norm:
        screen_x = tx_norm * w
        screen_y = ty_norm * h

        rx = 0.35 + tx_norm * 0.30 + np.random.normal(0.0, 0.001)
        ry = 0.35 + ty_norm * 0.30 + np.random.normal(0.0, 0.001)
        yaw = (tx_norm - 0.50) * 10.0 + np.random.normal(0.0, 0.05)
        pitch = (ty_norm - 0.50) * 8.0 + np.random.normal(0.0, 0.05)

        sample = CalibrationPointSample(
            target_screen_xy=(screen_x, screen_y),
            iris_ratio_x_mean=float(rx),
            iris_ratio_y_mean=float(ry),
            head_yaw_mean=float(yaw),
            head_pitch_mean=float(pitch),
            sample_count=30
        )
        samples.append(sample)

    res = calibrator.solve(samples)

    assert res.is_valid is True
    assert res.rmse_pixels <= 35.0
    assert len(res.affine_matrix_3x3) == 2
    assert len(res.poly_weights_2x6) == 2

    # Test polynomial prediction
    mid_u, mid_v = calibrator.apply_polynomial_gaze(
        np.array(res.poly_weights_2x6),
        iris_rx=0.50,
        iris_ry=0.50,
        head_yaw=0.0,
        head_pitch=0.0,
        screen_width=w,
        screen_height=h
    )
    # Mid point (0.5, 0.5) maps near screen center (960, 540)
    assert abs(mid_u - 960.0) < 50.0
    assert abs(mid_v - 540.0) < 50.0
