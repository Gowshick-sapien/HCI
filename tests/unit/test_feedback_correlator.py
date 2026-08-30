"""
Unit tests for Layer 4 Temporal Feedback Correlator.
Verifies Invariants INV-D4.4 and INV-D4.5.
"""

import pytest

from src.feedback.feedback_correlator import FeedbackCorrelator
from src.storage.schemas import (
    ActionContext,
    ActionTier,
    FailureMode,
    FailureSeverity,
    FeedbackEvent,
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


def test_refractory_period_suppression_invariant():
    """Invariant INV-D4.4: Events within refractory window (< 200 ms) are strictly suppressed."""
    correlator = FeedbackCorrelator(refractory_period_sec=0.20)
    t0 = 500.0
    action = _create_mock_action(t0=t0)
    correlator.register_action(action)

    # Raw feedback event fired 0.08s after action (during physical follow-through)
    raw_event = FeedbackEvent(
        feedback_id="fb_fast",
        action_id="act_001",
        timestamp=t0 + 0.08,
        latency_delta_t=0.08,
        feedback_type=FeedbackType.IMPLICIT_NEG,
        confidence_cfb=0.90,
        failure_mode=FailureMode.USER_OVERRIDE,
        severity=FailureSeverity.SEV_2_MINOR,
        detector_source="TEST_TAKEOVER"
    )

    result = correlator.process_feedback_event(raw_event, current_time=t0 + 0.08)
    assert result is None, "Refractory period (< 200ms) must suppress early micro-events"


def test_stability_expiration_positive_feedback_invariant():
    """Invariant INV-D4.5: Actions uncontested past 2000 ms resolve to IMPLICIT_POS."""
    correlator = FeedbackCorrelator(correction_window_sec=2.00)
    t0 = 500.0
    action = _create_mock_action(t0=t0, action_id="act_steady")
    correlator.register_action(action)

    # Check at t0 + 1.0s (still active)
    exp_early = correlator.check_stability_expirations(current_time=t0 + 1.00)
    assert len(exp_early) == 0

    # Check at t0 + 2.1s (stability expired)
    exp_done = correlator.check_stability_expirations(current_time=t0 + 2.10)
    assert len(exp_done) == 1
    assert exp_done[0].action_id == "act_steady"
    assert exp_done[0].feedback_type == FeedbackType.IMPLICIT_POS
    assert exp_done[0].failure_mode == FailureMode.NONE
