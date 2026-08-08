"""
Unit Tests for Calibration Geometry Utilities.
Verifies affine gaze fitting, Mahalanobis distance, and 3D neutral posture ellipsoid bounds.
"""

import numpy as np
import pytest

from src.utils.geometry import (
    apply_affine_gaze,
    compute_mahalanobis_distance,
    euler_to_rotation_matrix,
    fit_affine_gaze_matrix,
    fit_neutral_pose_ellipsoid,
    is_in_neutral_ellipsoid,
)


def test_fit_affine_gaze_matrix_exact():
    """Affine solver must accurately reconstruct known linear mapping."""
    # Known transformation: u = 1920 * rx, v = 1080 * ry
    pupil_pts = [(0.1, 0.1), (0.9, 0.1), (0.5, 0.5), (0.1, 0.9), (0.9, 0.9)]
    screen_pts = [(192.0, 108.0), (1728.0, 108.0), (960.0, 540.0), (192.0, 972.0), (1728.0, 972.0)]

    M, rmse = fit_affine_gaze_matrix(pupil_pts, screen_pts)

    assert rmse < 1e-4
    assert M.shape == (2, 3)

    # Test projection on center point
    u, v = apply_affine_gaze(M, 0.5, 0.5)
    assert u == pytest.approx(960.0, abs=1e-3)
    assert v == pytest.approx(540.0, abs=1e-3)


def test_fit_neutral_pose_ellipsoid_and_mahalanobis():
    """Ellipsoid fitting must produce invertible covariance and identify resting posture."""
    np.random.seed(42)
    # Generate 50 synthetic neutral posture samples around (0, 0, 0)
    samples = [(float(x), float(y), float(z)) for x, y, z in np.random.normal(0.0, 1.0, size=(50, 3))]

    mean_vec, cov_inv = fit_neutral_pose_ellipsoid(samples)

    assert mean_vec.shape == (3,)
    assert cov_inv.shape == (3, 3)

    # Center of distribution should have near-zero Mahalanobis distance
    d_center = compute_mahalanobis_distance((float(mean_vec[0]), float(mean_vec[1]), float(mean_vec[2])), mean_vec, cov_inv)
    assert d_center == pytest.approx(0.0, abs=1e-4)

    # Center is inside the 95% ellipsoid
    assert is_in_neutral_ellipsoid((float(mean_vec[0]), float(mean_vec[1]), float(mean_vec[2])), mean_vec, cov_inv) is True

    # Extreme posture outlier (e.g. 50 degrees yaw) is outside the 95% ellipsoid
    assert is_in_neutral_ellipsoid((50.0, 50.0, 50.0), mean_vec, cov_inv) is False


def test_euler_to_rotation_matrix_identity():
    """Zero Euler angles should yield identity rotation matrix."""
    R = euler_to_rotation_matrix(0.0, 0.0, 0.0)
    assert np.allclose(R, np.eye(3))
