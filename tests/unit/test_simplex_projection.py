"""
Unit tests for Exact 1D Box-Constrained Simplex Projection Engine.
Verifies Invariants INV-D2.1, INV-D2.2, and Monte Carlo probability axioms.
"""

import numpy as np
import pytest

from src.fusion.simplex_projection import SimplexProjectionEngine


def test_simplex_projection_sum_and_non_negativity_invariants():
    """Invariant INV-D2.1 & INV-D2.2: Sum equals 1.0 (+-1e-9) and all w_i >= 0.0."""
    np.random.seed(42)

    # 1,000 Monte Carlo test vectors with arbitrary values (positive, negative, zero, extreme)
    for _ in range(1000):
        k = np.random.randint(2, 10)
        y = np.random.uniform(-100.0, 100.0, size=k)

        w = SimplexProjectionEngine.project_simplex_1d(y)

        # Invariant 1: Sum to 1.0 within float precision
        assert abs(float(np.sum(w)) - 1.0) <= 1e-9

        # Invariant 2: Non-negativity
        assert np.all(w >= 0.0)

        # Invariant 3: Output dimension matches input dimension
        assert w.shape == (k,)


def test_simplex_projection_uniform_and_extreme_cases():
    # Identical inputs should produce uniform distribution
    y_uniform = [5.0, 5.0, 5.0]
    w_uniform = SimplexProjectionEngine.project_simplex_1d(y_uniform)
    assert np.allclose(w_uniform, [1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0], atol=1e-8)

    # Dominant single entry
    y_dominant = [1000.0, -100.0, -200.0]
    w_dominant = SimplexProjectionEngine.project_simplex_1d(y_dominant)
    assert w_dominant[0] == pytest.approx(1.0, abs=1e-7)
    assert w_dominant[1] == 0.0
    assert w_dominant[2] == 0.0


def test_simplex_projection_epsilon_floor():
    y = [10.0, 0.0, 0.0]
    eps = 0.05
    w = SimplexProjectionEngine.project_simplex_1d(y, epsilon_floor=eps)

    assert abs(float(np.sum(w)) - 1.0) <= 1e-9
    assert np.all(w >= eps - 1e-9)


def test_simplex_projection_batch():
    batch_y = np.random.randn(50, 4)
    batch_w = SimplexProjectionEngine.project_simplex_batch(batch_y)

    assert batch_w.shape == (50, 4)
    for i in range(50):
        assert abs(float(np.sum(batch_w[i])) - 1.0) <= 1e-9
        assert np.all(batch_w[i] >= 0.0)
