"""
Unit tests for HealthBadgeRenderer (Deliverable E2).
Verifies Invariant INV-E2.5: Color palette mapping and text layout across all health states and device modes.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
from src.storage.schemas import DeviceMode, SystemHealthState
from src.ui.health_badge_renderer import HealthBadgeRenderer


def test_health_badge_palette_mapping():
    """Invariant INV-E2.5: Health states map to valid display strings and non-empty QColors."""
    renderer = HealthBadgeRenderer()

    states = [
        SystemHealthState.BOOTSTRAPPING,
        SystemHealthState.LEARNING,
        SystemHealthState.IMPROVING,
        SystemHealthState.STABLE,
        SystemHealthState.DRIFTING,
        SystemHealthState.RECOVERING,
    ]

    for state in states:
        color, label = renderer.get_health_palette(state)
        assert label == state.value
        assert color.isValid()
        assert color.alpha() > 0


def test_device_mode_palette_mapping():
    """Invariant INV-E2.5: Device modes produce valid color palettes and readable badges."""
    renderer = HealthBadgeRenderer()

    modes = [
        DeviceMode.GESTURE,
        DeviceMode.MOUSE_PRIORITY,
        DeviceMode.KEYBOARD,
        DeviceMode.NO_ACTION,
    ]

    for mode in modes:
        color, label = renderer.get_device_mode_palette(mode)
        assert len(label) > 0
        assert color.isValid()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
