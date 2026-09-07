"""
Unit tests for SPRTTrajectoryGauge (Deliverable E3).
Verifies Invariant INV-E3.4: Cumulative SPRT score updates, boundary alerts, and reset logic.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.sprt_trajectory_gauge import SPRTTrajectoryCanvas, SPRTTrajectoryGauge


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_sprt_gauge_score_updates_and_alarm(qapp):
    """Invariant INV-E3.4: Cumulative SPRT score updates and alarm flag transitions."""
    canvas = SPRTTrajectoryCanvas(threshold_a=2.89, threshold_b=-2.25, max_history=50)

    # Initial score
    assert canvas._current_score == 0.0
    assert not canvas._alarm_active

    # Push score below threshold A
    canvas.push_score(1.50, is_alarm=False)
    assert canvas._current_score == 1.50
    assert not canvas._alarm_active

    # Push score >= 2.89 with alarm
    canvas.push_score(3.10, is_alarm=True)
    assert canvas._current_score == 3.10
    assert canvas._alarm_active

    # Reset
    canvas.reset()
    assert canvas._current_score == 0.0
    assert not canvas._alarm_active


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
