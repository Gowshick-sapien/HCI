"""
Integration test for Explainability HUD Pipeline (Deliverable E2).
Verifies Invariant INV-E2.6: Seamless data propagation from Perception & Adaptation into HUDManager.
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
from PySide6.QtWidgets import QApplication

from src.storage.schemas import (
    ActionType,
    AssessmentMetrics,
    ComposedCommand,
    DeviceMode,
    EyeLandmarks,
    GestureToken,
    HandLandmarks,
    HeadPoseLandmarks,
    PerceptionFrame,
    SystemHealthState,
)
from src.ui.hud_manager import HUDManager


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_hud_manager_pipeline_integration(qapp):
    """Invariant INV-E2.6: Telemetry flows smoothly into HUDManager without deadlocks."""
    manager = HUDManager(screen_width=1280, screen_height=720, enable_overlay=True)
    overlay = manager.initialize_overlay()
    assert overlay is not None

    perc_frame = PerceptionFrame(
        timestamp_ms=1000.0,
        frame_id=1,
        eye=EyeLandmarks((320.0, 240.0), (340.0, 240.0), 0.28, 0.28, 0.5, 0.5, 0.85),
        head=HeadPoseLandmarks(0.0, 0.0, 0.0, (0.0, 0.0, 0.0), 0.1, 0.90),
        hand=HandLandmarks(True, 0.02, (0.0, 0.0, 1.0), (640.0, 480.0, 0.0), 0.0, "PINCH_INDEX", 0.88),
        gaze_confidence=0.85,
        head_confidence=0.90,
        gaze_screen_xy=(640.0, 360.0),
        head_euler_angles=(0.0, 0.0, 0.0),
        gaze_dwell_ms=350.0,
        gaze_stability=0.92,
        gaze_anchor=(640.0, 360.0)
    )

    metrics = AssessmentMetrics(
        timestamp=time.time(),
        interactions_count=12,
        adaptation_gain_ewma=0.04,
        learning_velocity=0.02,
        weight_stability_index=0.88,
        adaptation_confidence_index=0.82,
        expected_calibration_error=0.06,
        recovery_rate=1.0,
        drift_recovery_time=0.0,
        health_state=SystemHealthState.STABLE
    )

    command = ComposedCommand(
        action_id="cmd_integ_01",
        action_type=ActionType.PRIMARY_CLICK,
        gaze_anchor=(640.0, 360.0),
        gesture_token=GestureToken.PINCH_INDEX,
        c_target=0.85,
        c_gesture=0.88,
        composed_score=0.86,
        requires_gaze_target=True,
        timestamp_ms=1000.0
    )

    # Push updates
    manager.update_frame(
        perception=perc_frame,
        command=command,
        metrics=metrics,
        device_mode=DeviceMode.GESTURE,
        weights={"EYE": 0.40, "HEAD": 0.30, "HAND": 0.30}
    )

    # Verify state inside overlay
    assert overlay._current_perception is not None
    assert overlay._current_command.action_type == ActionType.PRIMARY_CLICK
    assert overlay._current_metrics.health_state == SystemHealthState.STABLE
    assert overlay._active_device_mode == DeviceMode.GESTURE

    manager.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
