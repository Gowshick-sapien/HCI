"""
Geometric and Calibration Geometry Utilities.
Provides affine gaze perspective solvers, 3D Euler/Rotation conversions,
and Mahalanobis neutral pose ellipsoid estimation.
"""

from typing import List, Tuple
import numpy as np


def fit_affine_gaze_matrix(
    pupil_coords: List[Tuple[float, float]],
    screen_coords: List[Tuple[float, float]]
) -> Tuple[np.ndarray, float]:
    """
    Fits a 2x3 affine transformation matrix M_gaze mapping pupil ratio coordinates (r_x, r_y)
    to screen coordinates (u, v) via Ordinary Least Squares:
    [u, v]^T = M_gaze * [r_x, r_y, 1]^T

    Returns:
        (M_gaze, rmse): 2x3 affine matrix and root-mean-square error in screen pixels.
    """
    if len(pupil_coords) < 3 or len(pupil_coords) != len(screen_coords):
        raise ValueError("At least 3 matching point pairs are required to fit an affine matrix.")

    n = len(pupil_coords)
    # Design matrix A: (n, 3) where each row is [r_x, r_y, 1]
    A = np.ones((n, 3), dtype=np.float64)
    for i, (rx, ry) in enumerate(pupil_coords):
        A[i, 0] = rx
        A[i, 1] = ry

    # Target matrix B: (n, 2) where each row is [u, v]
    B = np.array(screen_coords, dtype=np.float64)

    # Solve least squares: A * M^T = B  =>  M^T = (A^T A)^-1 A^T B
    M_T, residuals, rank, s = np.linalg.lstsq(A, B, rcond=None)
    M_gaze = M_T.T # (2, 3)

    # Compute prediction error RMSE
    pred_screen = np.dot(A, M_T)
    errors = np.linalg.norm(pred_screen - B, axis=1)
    rmse = float(np.sqrt(np.mean(errors ** 2)))

    return M_gaze, rmse


def apply_affine_gaze(M_gaze: np.ndarray, pupil_x: float, pupil_y: float) -> Tuple[float, float]:
    """Applies the 2x3 affine gaze matrix to map (pupil_x, pupil_y) to (u_screen, v_screen)."""
    homog_pupil = np.array([pupil_x, pupil_y, 1.0], dtype=np.float64)
    screen_pt = np.dot(M_gaze, homog_pupil)
    return float(screen_pt[0]), float(screen_pt[1])


def fit_neutral_pose_ellipsoid(
    pose_samples: List[Tuple[float, float, float]],
    regularization_eps: float = 1e-4
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Computes the 3D mean pose vector mu and inverted covariance matrix Sigma^-1 from sample poses.
    Adds a ridge regularization term to guarantee positive definiteness.

    Returns:
        (mean_vec, cov_inv): 3D mean array and 3x3 inverted covariance matrix.
    """
    if len(pose_samples) < 3:
        raise ValueError("At least 3 pose samples required to fit covariance.")

    samples = np.array(pose_samples, dtype=np.float64) # (N, 3)
    mean_vec = np.mean(samples, axis=0) # (3,)
    
    # Sample covariance
    cov = np.cov(samples, rowvar=False) # (3, 3)
    # Ridge regularization for numerical stability
    cov_reg = cov + regularization_eps * np.eye(3)
    
    cov_inv = np.linalg.inv(cov_reg)
    return mean_vec, cov_inv


def compute_mahalanobis_distance(
    pose: Tuple[float, float, float],
    mean_vec: np.ndarray,
    cov_inv: np.ndarray
) -> float:
    """Computes Mahalanobis distance d_M = sqrt((p - mu)^T * Sigma^-1 * (p - mu))."""
    diff = np.array(pose, dtype=np.float64) - mean_vec
    d_sq = float(np.dot(diff.T, np.dot(cov_inv, diff)))
    return float(np.sqrt(max(0.0, d_sq)))


def is_in_neutral_ellipsoid(
    pose: Tuple[float, float, float],
    mean_vec: np.ndarray,
    cov_inv: np.ndarray,
    chi2_threshold: float = 7.815
) -> bool:
    """
    Evaluates whether the given 3D pose lies within the 95% confidence neutral ellipsoid:
    (p - mu)^T * Sigma^-1 * (p - mu) <= chi2_3(0.95) ~= 7.815.
    """
    diff = np.array(pose, dtype=np.float64) - mean_vec
    d_sq = float(np.dot(diff.T, np.dot(cov_inv, diff)))
    return bool(d_sq <= chi2_threshold)


def euler_to_rotation_matrix(yaw: float, pitch: float, roll: float) -> np.ndarray:
    """Converts Euler angles (in degrees) to a 3x3 rotation matrix using ZYX convention."""
    y = np.radians(yaw)
    p = np.radians(pitch)
    r = np.radians(roll)

    R_z = np.array([[np.cos(y), -np.sin(y), 0], [np.sin(y), np.cos(y), 0], [0, 0, 1]])
    R_y = np.array([[np.cos(p), 0, np.sin(p)], [0, 1, 0], [-np.sin(p), 0, np.cos(p)]])
    R_x = np.array([[1, 0, 0], [0, np.cos(r), -np.sin(r)], [0, np.sin(r), np.cos(r)]])

    return np.dot(R_z, np.dot(R_y, R_x))
