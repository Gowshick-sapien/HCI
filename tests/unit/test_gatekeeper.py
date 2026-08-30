"""
Unit tests for Engine 5B: Gatekeeper SPRT Validator.
Verifies Invariant INV-D5.2.
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest

from src.adaptation.gatekeeper import Gatekeeper
from src.storage.schemas import (
    FailureMode,
    FailureSeverity,
    FeedbackEvent,
    FeedbackType,
    GatekeeperVerdict,
)


def _make_event(is_neg: bool, conf: float = 0.85, mode: FailureMode = FailureMode.USER_OVERRIDE) -> FeedbackEvent:
    return FeedbackEvent(
        feedback_id="fb_sprt_01",
        action_id="cmd_01",
        timestamp=time.time(),
        latency_delta_t=0.5,
        feedback_type=FeedbackType.IMPLICIT_NEG if is_neg else FeedbackType.IMPLICIT_POS,
        confidence_cfb=conf,
        failure_mode=mode if is_neg else FailureMode.NONE,
        severity=FailureSeverity.SEV_2_MINOR,
        detector_source="TEST_DETECTOR"
    )


def test_gatekeeper_rejects_low_confidence():
    """Invariant INV-D5.2: Gatekeeper immediately rejects feedback with confidence < threshold."""
    gatekeeper = Gatekeeper(min_confidence_threshold=0.65)
    event = _make_event(is_neg=True, conf=0.50)

    decision = gatekeeper.evaluate_feedback(event)
    assert decision.verdict == GatekeeperVerdict.REJECT
    assert "Confidence 0.50 < threshold" in str(decision.rejection_reason)


def test_gatekeeper_rejects_single_isolated_event():
    """Invariant INV-D5.2: Gatekeeper requires minimum sample evidence before approving."""
    gatekeeper = Gatekeeper(min_samples=3)
    event = _make_event(is_neg=True, conf=0.85)

    decision = gatekeeper.evaluate_feedback(event)
    assert decision.verdict == GatekeeperVerdict.REJECT
    assert decision.effective_learning_rate_scale == 0.0


def test_gatekeeper_approves_sustained_systematic_bias():
    """Invariant INV-D5.2: SPRT approves updates upon cumulative evidence exceeding upper threshold."""
    gatekeeper = Gatekeeper(min_samples=3, alpha_type1=0.05, beta_type2=0.10)

    # Feed consecutive high-confidence negative feedback
    decisions = []
    for _ in range(4):
        event = _make_event(is_neg=True, conf=0.90)
        dec = gatekeeper.evaluate_feedback(event)
        decisions.append(dec)

    # At least one decision must achieve approval once threshold is crossed
    approved_decisions = [d for d in decisions if d.verdict == GatekeeperVerdict.APPROVE]
    assert len(approved_decisions) >= 1
    assert approved_decisions[0].effective_learning_rate_scale > 0.50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

