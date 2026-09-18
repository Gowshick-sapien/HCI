"""
Unit tests for OneEuroFilter implementation.
"""

import numpy as np
import pytest

from src.perception.one_euro_filter import OneEuroFilter


def test_one_euro_filter_constant_input():
    """Constant input remains constant."""
    filt = OneEuroFilter(fc_min=0.8, beta=0.007, d_cutoff=1.0)
    for i in range(50):
        t = i * (1.0 / 60.0)
        out = filt.update([100.0, 200.0], timestamp_sec=t)
    assert np.allclose(out, [100.0, 200.0], atol=1e-3)


def test_one_euro_filter_step_response():
    """Step input converges to the new steady state."""
    filt = OneEuroFilter(fc_min=0.8, beta=0.007, d_cutoff=1.0)
    # Initial steady state at 0.0
    for i in range(20):
        filt.update([0.0, 0.0], timestamp_sec=i * 0.016)
    # Step change to 100.0
    out = None
    for i in range(20, 150):
        out = filt.update([100.0, 100.0], timestamp_sec=i * 0.016)
    assert np.allclose(out, [100.0, 100.0], atol=1.0)


def test_one_euro_filter_noise_attenuation():
    """High-frequency jitter is smoothed out: output variance < input variance."""
    filt = OneEuroFilter(fc_min=0.8, beta=0.007, d_cutoff=1.0)
    np.random.seed(42)
    noise_sigma = 10.0
    inputs = []
    outputs = []

    for i in range(200):
        t = i * (1.0 / 60.0)
        raw_val = 500.0 + np.random.normal(0.0, noise_sigma)
        inputs.append(raw_val)
        filtered = filt.update([raw_val, raw_val], timestamp_sec=t)
        outputs.append(filtered[0])

    # Discard warm-up frames
    in_var = np.var(inputs[20:])
    out_var = np.var(outputs[20:])
    assert out_var < in_var * 0.25


def test_one_euro_filter_fast_ramp_tracking():
    """Fast motion leads to higher cutoff frequency and responsive tracking."""
    filt = OneEuroFilter(fc_min=0.8, beta=0.05, d_cutoff=1.0)
    speed = 1000.0  # px/s
    dt = 1.0 / 60.0

    # Let the ramp run for 1 second
    current_pos = 0.0
    lag_errors = []
    for i in range(60):
        t = i * dt
        current_pos = t * speed
        filtered = filt.update([current_pos], timestamp_sec=t)
        if i > 15:  # past initial transient
            lag_errors.append(abs(current_pos - filtered[0]))

    mean_lag = np.mean(lag_errors)
    # Average lag during high speed motion should remain small
    assert mean_lag < 50.0
