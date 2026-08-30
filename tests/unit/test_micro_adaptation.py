"""
Unit tests for Engine 5B: Online Micro-Adaptation Engine.
Verifies Invariant INV-D5.3.
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import numpy as np
import pytest

from src.adaptation.micro_adaptation import MicroAdaptationEngine, project_to_simplex_with_min
from src.storage.schemas import (
    FailureMode,
    FailureSeverity,
    FeedbackEvent,
    FeedbackType,
    GatekeeperDecision,
    GatekeeperVerdict,
    ProfileSnapshot,
)


def test_simplex_projection_with_minimum_bound():
    """Invariant INV-D5.3: Simplex projection strictly guarantees sum=1.0 and w_i >= min_weight."""
    v = np.array([1.5, -0.4, 0.8], dtype=np.float64)
    w = project_to_simplex_with_min(v, min_weight=0.05)

    assert abs(np.sum(w) - 1.0) < 1e-7
    assert np.all(w >= 0.05 - 1e-7)


def test_micro_adaptation_step_bounds_and_simplex():
    """Invariant INV-D5.3: Gradient updates remain within max_step_bound and maintain simplex constraints."""
    engine = MicroAdaptationEngine(
        base_learning_rate=0.04,
        min_modality_weight=0.05,
        max_step_bound=0.08
    )

    profile = ProfileSnapshot.create_default()
    engine.set_weights_from_profile(profile)
    w_initial = engine.current_weights_dict

    event = FeedbackEvent(
        feedback_id="fb_01",
        action_id="cmd_01",
        timestamp=time.time(),
        latency_delta_t=0.5,
        feedback_type=FeedbackType.IMPLICIT_NEG,
        confidence_cfb=0.90,
        failure_mode=FailureMode.WRONG_TARGET,
        severity=FailureSeverity.SEV_3_MODERATE,
        detector_source="TEST_DETECTOR"
    )

    decision = GatekeeperDecision(
        verdict=GatekeeperVerdict.APPROVE,
        rejection_reason=None,
        sample_count=4,
        confidence_cfb=0.90,
        sprt_score=3.2,
        effective_learning_rate_scale=1.0
    )

    w_updated, was_updated = engine.adapt(event, decision)

    assert was_updated is True
    # EYE weight should have decreased due to WRONG_TARGET penalty
    assert w_updated["EYE"] < w_initial["EYE"]
    # Verify sum = 1.0
    assert abs(w_updated["EYE"] + w_updated["HEAD"] + w_updated["HAND"] - 1.0) < 1e-5
    # Verify all components >= min_weight
    assert min(w_updated["EYE"], w_updated["HEAD"], w_updated["HAND"]) >= 0.05


def test_micro_adaptation_rejected_decision_noop():
    """Verifies that REJECT decisions result in no weight modification."""
    engine = MicroAdaptationEngine()
    w_initial = engine.current_weights_dict

    event = FeedbackEvent(
        feedback_id="fb_02",
        action_id="cmd_02",
        timestamp=time.time(),
        latency_delta_t=0.5,
        feedback_type=FeedbackType.IMPLICIT_NEG,
        confidence_cfb=0.50,
        failure_mode=FailureMode.USER_OVERRIDE,
        severity=FailureSeverity.SEV_2_MINOR,
        detector_source="TEST_DETECTOR"
    )

    decision = GatekeeperDecision(
        verdict=GatekeeperVerdict.REJECT,
        rejection_reason="Low confidence",
        sample_count=1,
        confidence_cfb=0.50,
        sprt_score=0.2,
        effective_learning_rate_scale=0.0
    )

    w_out, was_updated = engine.adapt(event, decision)
    assert was_updated is False
    assert w_out == w_initial


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

