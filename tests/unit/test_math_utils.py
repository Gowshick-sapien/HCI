"""
Unit Tests for Mathematical Optimization Utilities.
Verifies box-constrained simplex projection, EWMA smoothing, ECE calculation, and clipping.
"""

import numpy as np
import pytest

from src.utils.math_utils import (
    ambiguity_gate,
    box_constrained_simplex_projection,
    clip_scalar,
    compute_ece,
    ewma_update,
    sigmoid,
    softmax,
)


def test_clip_scalar():
    """Scalar clipping must enforce bounds."""
    assert clip_scalar(1.5, 0.0, 1.0) == 1.0
    assert clip_scalar(-0.2, 0.0, 1.0) == 0.0
    assert clip_scalar(0.5, 0.0, 1.0) == 0.5


def test_sigmoid_numerical_stability():
    """Sigmoid must handle extreme inputs without overflow or underflow."""
    assert sigmoid(0.0) == 0.5
    assert sigmoid(1000.0) == pytest.approx(1.0, abs=1e-7)
    assert sigmoid(-1000.0) == pytest.approx(0.0, abs=1e-7)


def test_softmax_properties():
    """Softmax output must be positive and sum to 1.0."""
    x = np.array([1.0, 2.0, 3.0])
    sm = softmax(x)
    assert np.all(sm > 0.0)
    assert np.sum(sm) == pytest.approx(1.0)


def test_ewma_update():
    """EWMA must smoothly interpolate between prior and current observations."""
    prev = 10.0
    curr = 20.0
    # alpha = 0.10 => 0.10 * 20 + 0.90 * 10 = 2 + 9 = 11.0
    assert ewma_update(curr, prev, alpha=0.10) == pytest.approx(11.0)


def test_ambiguity_gate():
    """Ambiguity gate g_weight(S_a, theta_a) matches the specified logistic formula."""
    # When score == threshold (diff = 0), g_weight = 1 / (1 + exp(2.0)) ~= 0.1192
    gate_at_boundary = ambiguity_gate(0.60, 0.60, steepness=40.0, delta=0.05)
    assert gate_at_boundary == pytest.approx(1.0 / (1.0 + np.exp(2.0)), abs=1e-4)

    # When score >> threshold (diff >> 0.05), g_weight approaches 1.0
    gate_far = ambiguity_gate(0.95, 0.60, steepness=40.0, delta=0.05)
    assert gate_far == pytest.approx(1.0, abs=1e-3)
    assert gate_far > gate_at_boundary


def test_box_constrained_simplex_projection_basic():
    """Simplex projection must satisfy sum = 1.0 and box bounds [0.05, 0.85]."""
    raw_weights = np.array([0.90, 0.20, 0.10])
    proj = box_constrained_simplex_projection(raw_weights, l=0.05, u=0.85, target_sum=1.0)

    assert np.sum(proj) == pytest.approx(1.0, abs=1e-6)
    assert np.all(proj >= 0.05 - 1e-6)
    assert np.all(proj <= 0.85 + 1e-6)


def test_box_constrained_simplex_projection_extreme():
    """Simplex projection must handle extreme outliers and uniform inputs."""
    # Extreme single component
    raw_weights = np.array([5.0, -2.0, 0.0])
    proj = box_constrained_simplex_projection(raw_weights, l=0.05, u=0.85, target_sum=1.0)

    assert np.sum(proj) == pytest.approx(1.0, abs=1e-6)
    assert np.all(proj >= 0.05 - 1e-6)
    assert np.all(proj <= 0.85 + 1e-6)
    # Largest raw weight gets upper bound
    assert proj[0] == pytest.approx(0.85, abs=1e-4)


def test_compute_ece():
    """ECE should be 0.0 for perfectly calibrated confidence."""
    confs = [0.8] * 10
    outcomes = [True] * 8 + [False] * 2
    ece = compute_ece(confs, outcomes, num_bins=10)
    assert ece == pytest.approx(0.0, abs=1e-2)
