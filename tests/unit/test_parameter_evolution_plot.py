"""
Unit tests for ParameterEvolutionPlot & Canvas (Deliverable E3).
Verifies Invariant INV-E3.3: Weight trajectory tracking, history queue bounds, and reset behavior.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.parameter_evolution_plot import ParameterEvolutionCanvas, ParameterEvolutionPlot


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_parameter_evolution_history_and_bounds(qapp):
    """Invariant INV-E3.3: Maintains bounded history queues and updates modality weights."""
    canvas = ParameterEvolutionCanvas(max_history=50)

    # Initial history contains 15 baseline samples
    assert len(canvas._eye_history) == 15
    assert canvas._eye_history[-1] == 0.40

    # Push updated weights
    canvas.push_weights({"EYE": 0.25, "HEAD": 0.45, "HAND": 0.30}, force=True)
    assert canvas._eye_history[-1] == 0.25
    assert canvas._head_history[-1] == 0.45
    assert canvas._hand_history[-1] == 0.30

    # Push 100 samples to verify max_history queue limit
    for _ in range(100):
        canvas.push_weights({"EYE": 0.20, "HEAD": 0.50, "HAND": 0.30}, force=True)

    assert len(canvas._eye_history) == 50
    assert len(canvas._head_history) == 50
    assert len(canvas._hand_history) == 50

    # Reset
    canvas.clear_history()
    assert len(canvas._eye_history) == 15
    assert canvas._eye_history[0] == 0.40


def test_parameter_evolution_plot_container(qapp):
    """Verifies that ParameterEvolutionPlot container embeds canvas and updates correctly."""
    plot_widget = ParameterEvolutionPlot()
    plot_widget.update_weights({"EYE": 0.35, "HEAD": 0.35, "HAND": 0.30})

    assert plot_widget.canvas._eye_history[-1] == 0.35
    assert plot_widget.canvas._head_history[-1] == 0.35


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
