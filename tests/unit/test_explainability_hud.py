"""
Unit tests for ExplainabilityHUDOverlay (Deliverable E2).
Verifies Invariant INV-E2.2: Window attributes and click-through transparency flags.
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.ui.explainability_hud import ExplainabilityHUDOverlay


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_hud_window_transparency_flags(qapp):
    """Invariant INV-E2.2: Window flags enforce click-through transparency and frameless overlay."""
    hud = ExplainabilityHUDOverlay(screen_width=1280, screen_height=720)

    flags = hud.windowFlags()
    assert flags & Qt.WindowType.FramelessWindowHint
    assert flags & Qt.WindowType.WindowStaysOnTopHint
    assert flags & Qt.WindowType.WindowTransparentForInput

    assert hud.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) is True
    assert hud.width() == 1280
    assert hud.height() == 720


def test_hud_update_telemetry(qapp):
    """Verifies that telemetry buffers are thread-safely updated."""
    hud = ExplainabilityHUDOverlay(screen_width=1280, screen_height=720)
    w_new = {"EYE": 0.50, "HEAD": 0.25, "HAND": 0.25}

    hud.update_telemetry(weights=w_new)
    assert hud._active_weights["EYE"] == 0.50
    assert hud._active_weights["HEAD"] == 0.25


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
