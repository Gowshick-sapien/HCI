"""
Unit tests for 3D Head Pose Neutral Ellipsoid Calibrator.
Verifies Invariant INV-D3.2: Positive-definiteness of regularized covariance.
"""

import numpy as np
import pytest

from src.calibration.head_pose_calibrator import HeadPoseCalibrator


def test_head_pose_calibrator_positive_definiteness():
    """Invariant INV-D3.2: Covariance is positive definite (det > 0)."""
    calibrator = HeadPoseCalibrator(ridge_epsilon=1e-3)

    np.random.seed(42)
    # Generate 50 neutral posture samples centered around (0, 0, 0)
    samples = [
        (float(np.random.normal(1.0, 2.0)), float(np.random.normal(-2.0, 3.0)), float(np.random.normal(0.5, 1.5)))
        for _ in range(50)
    ]

    res = calibrator.fit(samples)
    assert res.is_positive_definite is True
    assert res.sample_count == 50

    # Covariance and precision must be 3x3
    cov = np.array(res.covariance_matrix_3x3)
    prec = np.array(res.precision_matrix_3x3)
    assert cov.shape == (3, 3)
    assert prec.shape == (3, 3)

    # Product of cov and precision should be identity matrix
    identity_approx = np.dot(cov, prec)
    assert np.allclose(identity_approx, np.eye(3), atol=1e-2)
