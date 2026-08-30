"""
Exact 1D Box-Constrained Simplex Projection Engine.
Implements the Michelot / Duchi O(K log K) deterministic Euclidean projection
onto the standard probability simplex Delta^K.
Guarantees exact sum-to-one constraint and non-negativity without Softmax distortion.
"""

from __future__ import annotations

from typing import Sequence, Union
import numpy as np


class SimplexProjectionEngine:
    """
    High-performance mathematical projection engine for probability simplices.
    Solves:
        argmin_{w in Delta^K} 0.5 * ||w - y||_2^2
        subject to sum_{i=1}^K w_i = 1, w_i >= 0 for all i in {1, ..., K}.
    """

    @staticmethod
    def project_simplex_1d(
        y: Union[np.ndarray, Sequence[float]],
        epsilon_floor: float = 0.0
    ) -> np.ndarray:
        """
        Projects an arbitrary 1D real vector y onto the standard probability simplex Delta^K.

        Args:
            y: Input real-valued vector of shape (K,).
            epsilon_floor: Optional minimum probability bound (Dirichlet regularizer >= 0).

        Returns:
            Projected weight vector w of shape (K,) satisfying sum(w) = 1.0 and w_i >= epsilon_floor.
        """
        y_arr = np.asarray(y, dtype=np.float64).flatten()
        k = y_arr.shape[0]

        if k == 0:
            raise ValueError("Cannot project an empty vector onto a simplex.")

        if k == 1:
            return np.array([1.0], dtype=np.float64)

        # 1. Sort vector in descending order: u_1 >= u_2 >= ... >= u_K
        u = np.sort(y_arr)[::-1]

        # 2. Compute cumulative sums of sorted components
        cssv = np.cumsum(u)

        # 3. Find optimal support index rho
        indices = np.arange(1, k + 1, dtype=np.float64)
        rho_condition = u + (1.0 - cssv) / indices > 0.0

        rho_indices = np.where(rho_condition)[0]
        if len(rho_indices) == 0:
            rho = 1
        else:
            rho = int(rho_indices[-1]) + 1

        # 4. Compute exact Lagrange multiplier lambda*
        theta = float((1.0 - cssv[rho - 1]) / float(rho))

        # 5. Compute Euclidean projection w = max(0, y + theta)
        w = np.maximum(y_arr + theta, 0.0)

        # 6. Apply strictly convex epsilon-floor Dirichlet shrinkage if requested
        if epsilon_floor > 0.0:
            floor_total = float(k * epsilon_floor)
            if floor_total < 1.0:
                w = (1.0 - floor_total) * w + epsilon_floor
            else:
                w = np.full(k, 1.0 / float(k), dtype=np.float64)

        # Strict floating-point sum-to-one precision guard
        sum_w = np.sum(w)
        if sum_w > 0.0:
            w = w / sum_w
        else:
            w = np.full(k, 1.0 / float(k), dtype=np.float64)

        return w

    @staticmethod
    def project_simplex_batch(
        y_batch: np.ndarray,
        epsilon_floor: float = 0.0
    ) -> np.ndarray:
        """
        Projects a 2D batch of weight vectors (N, K) onto the probability simplex row-wise.
        """
        y_arr = np.asarray(y_batch, dtype=np.float64)
        if y_arr.ndim != 2:
            raise ValueError(f"Expected 2D array of shape (N, K), got ndim={y_arr.ndim}")

        n_samples, k_dim = y_arr.shape
        w_batch = np.zeros_like(y_arr)

        for i in range(n_samples):
            w_batch[i] = SimplexProjectionEngine.project_simplex_1d(y_arr[i], epsilon_floor=epsilon_floor)

        return w_batch


__all__ = ["SimplexProjectionEngine"]
