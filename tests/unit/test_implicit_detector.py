"""
Unit tests for Layer 4 Implicit Feedback Detector.
Verifies Invariants INV-D4.1 and INV-D4.2.
"""

import time
import pytest

from src.feedback.implicit_detector import ImplicitFeedbackDetector
from src.storage.schemas import (
    ActionContext,
    ActionTier,
    FailureMode,
    FailureSeverity,
    FeedbackType,
)


def _create_mock_action(t0: float, action_id: str = "act_001") -> ActionContext:
    return ActionContext(
        action_id=action_id,
        action_name="PRIMARY_CLICK",
        tier=ActionTier.TIER_1_IMMEDIATE,
        timestamp_t0=t0,
        target_pid=1234,
        target_window_title="Test App",
        feature_snapshot=None,
        weights_snapshot={"GAZE": 0.4, "GESTURE": 0.6},
        fused_score=0.85,
        threshold=0.70,
        is_executed=True
    )


def test_mouse_takeover_detection_invariant():
    """Invariant INV-D4.1: Mouse displacement >= 16 px within 1.2s triggers IMPLICIT_NEG with USER_OVERRIDE."""
    detector = ImplicitFeedbackDetector(mouse_takeover_radius_px=16.0, mouse_takeover_window_sec=1.20)
    t0 = 100.0
    action = _create_mock_action(t0=t0)

    # 1. Displacement < 16 px -> None (ignored as minor tremor)
    event_sub = detector.evaluate_mouse_takeover(action, mouse_dx=5.0, mouse_dy=5.0, current_time=t0 + 0.50)
    assert event_sub is None

    # 2. Refractory period (< 0.20s) -> None (suppressed)
    event_ref = detector.evaluate_mouse_takeover(action, mouse_dx=30.0, mouse_dy=20.0, current_time=t0 + 0.10)
    assert event_ref is None

    # 3. Valid takeover within correction window (0.50s post-action)
    event_takeover = detector.evaluate_mouse_takeover(action, mouse_dx=20.0, mouse_dy=15.0, current_time=t0 + 0.50)
    assert event_takeover is not None
    assert event_takeover.feedback_type == FeedbackType.IMPLICIT_NEG
    assert event_takeover.failure_mode == FailureMode.USER_OVERRIDE
    assert event_takeover.confidence_cfb >= 0.75
    assert event_takeover.action_id == "act_001"

    # 4. Expired window (> 1.20s post-action) -> None
    event_exp = detector.evaluate_mouse_takeover(action, mouse_dx=30.0, mouse_dy=20.0, current_time=t0 + 1.50)
    assert event_exp is None


def test_keystroke_undo_detection_invariant():
    """Invariant INV-D4.2: Ctrl+Z within 2.0s triggers IMPLICIT_NEG with FALSE_ACTIVATION."""
    detector = ImplicitFeedbackDetector(undo_window_sec=2.00, escape_window_sec=1.50)
    t0 = 100.0
    action = _create_mock_action(t0=t0)

    # 1. Ctrl+Z within 0.8s
    event_undo = detector.evaluate_keystroke_undo(action, key_name="z", is_ctrl_pressed=True, current_time=t0 + 0.80)
    assert event_undo is not None
    assert event_undo.feedback_type == FeedbackType.IMPLICIT_NEG
    assert event_undo.failure_mode == FailureMode.FALSE_ACTIVATION
    assert event_undo.severity == FailureSeverity.SEV_3_MODERATE
    assert event_undo.confidence_cfb == 0.95

    # 2. Escape key within 1.0s
    event_esc = detector.evaluate_keystroke_undo(action, key_name="escape", is_ctrl_pressed=False, current_time=t0 + 1.00)
    assert event_esc is not None
    assert event_esc.failure_mode == FailureMode.WRONG_TARGET

    # 3. Unrelated key (e.g. 'a')
    event_norm = detector.evaluate_keystroke_undo(action, key_name="a", is_ctrl_pressed=False, current_time=t0 + 0.50)
    assert event_norm is None
