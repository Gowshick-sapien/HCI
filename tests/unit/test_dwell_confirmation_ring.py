"""
Unit tests for DwellConfirmationRing (Deliverable E2).
Verifies Invariant INV-E2.4: Circular progress angular sweeps and dwell timing calculations.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
from src.ui.dwell_confirmation_ring import DwellConfirmationRing


def test_dwell_ring_angular_sweep_calculation():
    """Invariant INV-E2.4: Calculates exact linear progress ratio and angular sweep in degrees."""
    ring = DwellConfirmationRing(dwell_confirmation_threshold_ms=600.0)

    # 0 ms -> 0% -> 0 deg
    prog0, sweep0 = ring.calculate_sweep_angle(0.0)
    assert prog0 == 0.0
    assert sweep0 == 0.0

    # 300 ms -> 50% -> 180 deg
    prog1, sweep1 = ring.calculate_sweep_angle(300.0)
    assert abs(prog1 - 0.50) < 1e-4
    assert abs(sweep1 - 180.0) < 1e-4

    # 600 ms -> 100% -> 360 deg
    prog2, sweep2 = ring.calculate_sweep_angle(600.0)
    assert abs(prog2 - 1.00) < 1e-4
    assert abs(sweep2 - 360.0) < 1e-4

    # Overfill: 800 ms -> Clamped to 100% -> 360 deg
    prog3, sweep3 = ring.calculate_sweep_angle(800.0)
    assert abs(prog3 - 1.00) < 1e-4
    assert abs(sweep3 - 360.0) < 1e-4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
