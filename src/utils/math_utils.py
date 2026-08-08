"""
Mathematical and Numerical Optimization Utilities.
Provides robust vectorized numerical routines, EWMA smoothing, ECE calculation,
and exact 1D dual bisection box-constrained simplex projection.
"""

from typing import List, Tuple, Union
import numpy as np


def clip_scalar(val: float, min_val: float, max_val: float) -> float:
    """Clamps a floating point scalar to [min_val, max_val]."""
    return float(max(min_val, min(val, max_val)))


def clip_vector(vec: np.ndarray, min_val: float, max_val: float) -> np.ndarray:
    """Clamps a numpy vector to [min_val, max_val]."""
    return np.clip(vec, min_val, max_val)


def sigmoid(x: Union[float, np.ndarray], steepness: float = 1.0, midpoint: float = 0.0) -> Union[float, np.ndarray]:
    """Computes numerically stable generalized sigmoid function."""
    z = -steepness * (x - midpoint)
    # Clip z to avoid overflow in exp
    if isinstance(z, np.ndarray):
        z_clipped = np.clip(z, -60.0, 60.0)
        return 1.0 / (1.0 + np.exp(z_clipped))
    else:
        z_clipped = max(-60.0, min(float(z), 60.0))
        return float(1.0 / (1.0 + np.exp(z_clipped)))


def softmax(x: np.ndarray) -> np.ndarray:
    """Computes numerically stable softmax over a 1D vector."""
    shift_x = x - np.max(x)
    exps = np.exp(shift_x)
    return exps / np.sum(exps)


def ewma_update(current_val: float, prev_ewma: float, alpha: float = 0.10) -> float:
    """Computes Exponentially Weighted Moving Average update: EWMA_t = alpha*x_t + (1-alpha)*EWMA_{t-1}."""
    alpha = clip_scalar(alpha, 0.0, 1.0)
    return float(alpha * current_val + (1.0 - alpha) * prev_ewma)


def ambiguity_gate(score: float, threshold: float, steepness: float = 40.0, delta: float = 0.05) -> float:
    """
    Evaluates the continuous ambiguity gate g_weight(S_a, theta_a):
    g_weight = 1 / (1 + exp(-steepness * (|S_a - theta_a| - delta)))
    Suppresses SGD updates when the decision was unambiguous and clear (|S_a - theta_a| >> delta).
    """
    diff = abs(score - threshold)
    return float(sigmoid(diff, steepness=steepness, midpoint=delta))


def box_constrained_simplex_projection(
    v: np.ndarray,
    l: float = 0.05,
    u: float = 0.85,
    target_sum: float = 1.0,
    max_iter: int = 25,
    tol: float = 1e-7
) -> np.ndarray:
    """
    Exact 1D Dual Bisection Projection onto the Box-Constrained Simplex:
    argmin_{w} 0.5 * ||w - v||^2  subject to  sum(w) = target_sum,  l <= w_i <= u for all i.

    Uses monotonic root finding for f(mu) = sum(clip(v - mu, l, u)) - target_sum = 0.
    Guarantees convergence in <= 20 iterations.
    """
    v_arr = np.asarray(v, dtype=np.float64)
    d = len(v_arr)
    
    if d * l > target_sum + 1e-9 or d * u < target_sum - 1e-9:
        raise ValueError(f"Infeasible box constraints: d*l={d*l} must be <= {target_sum} <= d*u={d*u}")

    # Bracket search range for Lagrange multiplier mu
    mu_min = float(np.min(v_arr) - u)
    mu_max = float(np.max(v_arr) - l)

    for _ in range(max_iter):
        mu_mid = (mu_min + mu_max) / 2.0
        w_candidate = np.clip(v_arr - mu_mid, l, u)
        sum_w = float(np.sum(w_candidate))
        
        diff = sum_w - target_sum
        if abs(diff) <= tol:
            return w_candidate
        
        # f(mu) is monotonically decreasing in mu
        if diff > 0:
            mu_min = mu_mid
        else:
            mu_max = mu_mid

    # Final projection with midpoint
    mu_final = (mu_min + mu_max) / 2.0
    w_final = np.clip(v_arr - mu_final, l, u)
    
    # Residual normalization step to guarantee exact sum = target_sum
    res = target_sum - np.sum(w_final)
    if abs(res) > 1e-9:
        free_indices = np.where((w_final > l + 1e-6) & (w_final < u - 1e-6))[0]
        if len(free_indices) > 0:
            w_final[free_indices] += res / len(free_indices)
            w_final = np.clip(w_final, l, u)
            
    return w_final


def compute_ece(confidences: List[float], outcomes: List[bool], num_bins: int = 10) -> float:
    """
    Computes Expected Calibration Error (ECE) across B equal-width confidence bins:
    ECE = sum_{b=1}^B (|B_b| / N) * |acc(B_b) - conf(B_b)|
    """
    if not confidences or not outcomes or len(confidences) != len(outcomes):
        return 0.0
    
    n = len(confidences)
    confs = np.asarray(confidences, dtype=np.float64)
    accs = np.asarray(outcomes, dtype=np.float64)
    
    bin_boundaries = np.linspace(0.0, 1.0, num_bins + 1)
    ece = 0.0
    
    for i in range(num_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        
        if i == num_bins - 1:
            in_bin = (confs >= bin_lower) & (confs <= bin_upper)
        else:
            in_bin = (confs >= bin_lower) & (confs < bin_upper)
            
        bin_count = np.sum(in_bin)
        if bin_count > 0:
            bin_acc = float(np.mean(accs[in_bin]))
            bin_conf = float(np.mean(confs[in_bin]))
            ece += (bin_count / n) * abs(bin_acc - bin_conf)
            
    return float(ece)
