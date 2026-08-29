"""
Unit tests for Holt-Winters dynamic velocity-scaled smoothing filter.
"""

import numpy as np
import pytest

from src.perception.holt_winters_filter import HoltWintersFilter


def test_holt_winters_initialization_and_reset():
    hw = HoltWintersFilter(dim=2, alpha_0=0.25, beta=0.15)
    first_pt = [100.0, 200.0]
    out = hw.update(first_pt)
    assert np.allclose(out, [100.0, 200.0])

    hw.reset()
    assert hw._initialized is False


def test_holt_winters_stationary_jitter_attenuation():
    """Invariant INV-D1.2: Stationary coordinate jitter <= 1.2 px."""
    hw = HoltWintersFilter(dim=2, alpha_0=0.25, beta=0.15, gamma=0.01, alpha_min=0.20, alpha_max=0.85)
    
    np.random.seed(42)
    center = np.array([500.0, 500.0])
    raw_measurements = [center + np.random.normal(0.0, 2.0, 2) for _ in range(50)]

    smoothed_outputs = [hw.update(pt, velocity_magnitude=0.0) for pt in raw_measurements]
    
    # Compute std deviation of smoothed outputs after warm-up
    warmup = smoothed_outputs[15:]
    std_dev = np.std(warmup, axis=0)
    
    # Jitter std deviation should be bounded <= 1.2 px
    assert std_dev[0] <= 1.2
    assert std_dev[1] <= 1.2


def test_holt_winters_velocity_scaling():
    hw = HoltWintersFilter(dim=2, alpha_0=0.25, beta=0.15, gamma=0.02, alpha_min=0.20, alpha_max=0.85)
    
    # First frame initializes state
    hw.update([10.0, 10.0])
    
    # Second frame with zero velocity -> alpha reaches alpha_min
    hw.update([10.0, 10.0], velocity_magnitude=0.0)
    assert hw.last_alpha == 0.20

    # High-speed motion -> alpha scales up to alpha_max
    hw.update([100.0, 100.0], velocity_magnitude=50.0)
    assert hw.last_alpha == 0.85
