"""
Unit tests for ConfidenceBarsRenderer (Deliverable E2).
Verifies Invariant INV-E2.3: Modality confidence bar smoothing and bounds mapping.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
from src.ui.confidence_bars import ConfidenceBarsRenderer


def test_confidence_bars_smoothing():
    """Invariant INV-E2.3: Smooths high-frequency sensor updates via exponential filtering."""
    renderer = ConfidenceBarsRenderer(smoothing_alpha=0.50, bar_width=160.0)

    # First update: 0.0 -> 1.0 with alpha=0.5 yields 0.5
    smoothed = renderer.update_values(gaze_conf=1.0, head_conf=0.8, hand_conf=0.6)
    assert abs(smoothed[0] - 0.50) < 1e-4
    assert abs(smoothed[1] - 0.40) < 1e-4
    assert abs(smoothed[2] - 0.30) < 1e-4

    # Second update: 0.5 -> 1.0 with alpha=0.5 yields 0.75
    smoothed2 = renderer.update_values(gaze_conf=1.0, head_conf=0.8, hand_conf=0.6)
    assert abs(smoothed2[0] - 0.75) < 1e-4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
