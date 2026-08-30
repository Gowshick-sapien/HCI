"""
Integration test for Layer 4 Feedback Observer Pipeline.
Verifies end-to-end event flow: ActionContext -> Hardware Preemption -> Correlator -> Telemetry.
"""

from pathlib import Path
import pytest

from src.feedback.observer import FeedbackObserver
from src.feedback.telemetry_logger import FeedbackTelemetryLogger
from src.storage.schemas import (
    ActionContext,
    ActionTier,
    FailureMode,
    FeedbackEvent,
    FeedbackType,
)


def test_feedback_observer_pipeline_end_to_end(tmp_path: Path):
    """Verifies that an action execution followed by mouse takeover emits a correlated feedback event."""
    log_file = tmp_path / "integration_feedback.jsonl"
    logger = FeedbackTelemetryLogger(log_file_path=log_file)
    observer = FeedbackObserver(telemetry_logger=logger)

    received_events = []
    observer.register_feedback_listener(lambda ev: received_events.append(ev))

    t0 = 1000.0
    action = ActionContext(
        action_id="act_click_001",
        action_name="PRIMARY_CLICK",
        tier=ActionTier.TIER_1_IMMEDIATE,
        timestamp_t0=t0,
        target_pid=4321,
        target_window_title="Browser Window",
        feature_snapshot=None,
        weights_snapshot={"GAZE": 0.5, "GESTURE": 0.5},
        fused_score=0.88,
        threshold=0.75,
        is_executed=True
    )

    # 1. Register executed action
    observer.on_action_executed(action)

    # 2. Inject mouse takeover event at t0 + 0.60s
    ev = observer.on_mouse_movement(dx=35.0, dy=12.0, timestamp_sec=t0 + 0.60)

    assert ev is not None
    assert ev.action_id == "act_click_001"
    assert ev.feedback_type == FeedbackType.IMPLICIT_NEG
    assert ev.failure_mode == FailureMode.USER_OVERRIDE

    # 3. Verify listener received callback
    assert len(received_events) == 1
    assert received_events[0].feedback_id == ev.feedback_id

    # 4. Verify telemetry disk file
    logged = logger.read_recent_events(limit=5)
    assert len(logged) == 1
    assert logged[0]["action_id"] == "act_click_001"
