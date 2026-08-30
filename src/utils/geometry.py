"""
Geometric and Calibration Geometry Utilities.
Provides affine gaze perspective solvers, 3D Euler/Rotation conversions,
and Mahalanobis neutral pose ellipsoid estimation.
"""

from typing import List, Tuple, Union
import numpy as np


def fit_affine_gaze_matrix(
    pupil_coords: List[Tuple[float, float]],
    screen_coords: List[Tuple[float, float]],
    head_angles: List[Tuple[float, float]] = None
) -> Tuple[np.ndarray, float]:
    """
    Fits an affine transformation matrix M_gaze mapping pupil ratio coordinates (r_x, r_y)
    and optional head angles (yaw, pitch) to screen coordinates (u, v) via Ordinary Least Squares:
    [u, v]^T = M_gaze * [r_x, r_y, yaw, pitch, 1]^T

    Returns:
        (M_gaze, rmse): 2x3 or 2x5 affine matrix and root-mean-square error in screen pixels.
    """
    n = len(pupil_coords)
    if n < 3 or len(screen_coords) != n:
        raise ValueError("At least 3 matching point pairs are required to fit an affine matrix.")

    if head_angles and len(head_angles) == n:
        # Coupled Eye-Head Design matrix: (n, 5) -> [rx, ry, yaw, pitch, 1]
        A = np.ones((n, 5), dtype=np.float64)
        for i in range(n):
            A[i, 0] = pupil_coords[i][0]
            A[i, 1] = pupil_coords[i][1]
            A[i, 2] = head_angles[i][0]
            A[i, 3] = head_angles[i][1]
    else:
        # Pure Ocular Design matrix: (n, 3) -> [rx, ry, 1]
        A = np.ones((n, 3), dtype=np.float64)
        for i in range(n):
            A[i, 0] = pupil_coords[i][0]
            A[i, 1] = pupil_coords[i][1]

    B = np.array(screen_coords, dtype=np.float64)

    # Solve least squares: A * M^T = B  =>  M^T = (A^T A)^-1 A^T B
    M_T, residuals, rank, s = np.linalg.lstsq(A, B, rcond=None)
    M_gaze = M_T.T

    pred_screen = np.dot(A, M_T)
    errors = np.linalg.norm(pred_screen - B, axis=1)
    rmse = float(np.sqrt(np.mean(errors ** 2)))

    return M_gaze, rmse


def apply_affine_gaze(
    M_gaze: np.ndarray,
    pupil_x: float,
    pupil_y: float,
    head_yaw: float = 0.0,
    head_pitch: float = 0.0
) -> Tuple[float, float]:
    """
    Applies the affine gaze matrix to map (pupil_x, pupil_y, head_yaw, head_pitch) to (u_screen, v_screen).
    Dynamically supports 2x3, 3x3, 2x5, and 3x5 matrix representations.
    """
    M = np.asarray(M_gaze, dtype=np.float64)

    n_cols = M.shape[1] if M.ndim == 2 else 3

    if n_cols == 5:
        # Coupled Eye-Head vector: [rx, ry, yaw, pitch, 1.0]
        feat = np.array([pupil_x, pupil_y, head_yaw, head_pitch, 1.0], dtype=np.float64)
    elif n_cols == 6:
        # Polynomial 6-term: [1, rx, ry, rx^2, ry^2, rx*ry]
        feat = np.array([1.0, pupil_x, pupil_y, pupil_x ** 2, pupil_y ** 2, pupil_x * pupil_y], dtype=np.float64)
    elif n_cols == 9:
        # Polynomial Eye-Head 9-term
        feat = np.array([1.0, pupil_x, pupil_y, head_yaw, head_pitch, pupil_x**2, pupil_y**2, head_yaw**2, head_pitch**2], dtype=np.float64)
    else:
        # Standard Ocular vector: [rx, ry, 1.0]
        feat = np.array([pupil_x, pupil_y, 1.0], dtype=np.float64)

    screen_pt = np.dot(M[:2, :], feat)
    return float(screen_pt[0]), float(screen_pt[1])


def euler_to_rotation_matrix(yaw_deg: float, pitch_deg: float, roll_deg: float) -> np.ndarray:
    """Converts yaw, pitch, roll Euler angles (in degrees) to a 3x3 rotation matrix."""
    y = np.radians(yaw_deg)
    p = np.radians(pitch_deg)
    r = np.radians(roll_deg)

    R_z = np.array([[np.cos(y), -np.sin(y), 0], [np.sin(y), np.cos(y), 0], [0, 0, 1]], dtype=np.float64)
    R_y = np.array([[np.cos(p), 0, np.sin(p)], [0, 1, 0], [-np.sin(p), 0, np.cos(p)]], dtype=np.float64)
    R_x = np.array([[1, 0, 0], [0, np.cos(r), -np.sin(r)], [0, np.sin(r), np.cos(r)]], dtype=np.float64)

    return np.dot(R_z, np.dot(R_y, R_x))


def fit_neutral_pose_ellipsoid(
    pose_samples: List[Tuple[float, float, float]],
    regularization_eps: float = 1e-4
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Computes the 3D mean pose vector mu and inverted covariance matrix Sigma^-1 from sample poses.
    """
    if len(pose_samples) < 5:
        raise ValueError("At least 5 sample poses required to fit neutral pose ellipsoid.")

    samples_arr = np.array(pose_samples, dtype=np.float64)
    mu = np.mean(samples_arr, axis=0)

    centered = samples_arr - mu
    cov = np.cov(centered, rowvar=False)

    # Tikhonov regularization
    cov_reg = cov + np.eye(3, dtype=np.float64) * regularization_eps
    cov_inv = np.linalg.inv(cov_reg)

    return mu, cov_inv


def compute_mahalanobis_distance(
    pose: Tuple[float, float, float],
    mu: np.ndarray,
    cov_inv: np.ndarray
) -> float:
    """Computes Mahalanobis distance D_M from neutral pose distribution."""
    p = np.array(pose, dtype=np.float64)
    diff = p - mu
    d_sq = float(np.dot(np.dot(diff, cov_inv), diff))
    return float(np.sqrt(max(0.0, d_sq)))


def is_in_neutral_ellipsoid(
    pose: Tuple[float, float, float],
    mu: np.ndarray,
    cov_inv: np.ndarray,
    threshold: float = 3.0
) -> bool:
    """Checks if a 3D head pose falls within the neutral ellipsoid boundary (D_M <= threshold)."""
    return compute_mahalanobis_distance(pose, mu, cov_inv) <= threshold


# Alias for backward compatibility
mahalanobis_distance_3d = compute_mahalanobis_distance


__all__ = [
    "fit_affine_gaze_matrix",
    "apply_affine_gaze",
    "euler_to_rotation_matrix",
    "fit_neutral_pose_ellipsoid",
    "compute_mahalanobis_distance",
    "is_in_neutral_ellipsoid",
    "mahalanobis_distance_3d"
]
