"""
Multi-layer closed-loop integration test for Layer 5 Dual-Scale Dynamic Adaptation.
Verifies Invariant INV-D5.6: Full closed-loop feedback -> Assessment -> SPRT -> Micro-SGD -> Persistence.
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import numpy as np
import pytest

from src.adaptation.coordinator import AdaptationCoordinator
from src.storage.profile_manager import ProfileManager
from src.storage.schemas import (
    FailureMode,
    FailureSeverity,
    FeedbackEvent,
    FeedbackType,
    GatekeeperVerdict,
    SystemHealthState,
)


def _create_feedback(is_pos: bool, mode: FailureMode = FailureMode.NONE, conf: float = 0.85) -> FeedbackEvent:
    return FeedbackEvent(
        feedback_id="fb_integ_01",
        action_id="cmd_integ_01",
        timestamp=time.time(),
        latency_delta_t=0.50,
        feedback_type=FeedbackType.IMPLICIT_POS if is_pos else FeedbackType.IMPLICIT_NEG,
        confidence_cfb=conf,
        failure_mode=mode,
        severity=FailureSeverity.SEV_1_BENIGN if is_pos else FailureSeverity.SEV_3_MODERATE,
        detector_source="TEST_INTEG_DETECTOR"
    )


def test_closed_loop_adaptation_pipeline(tmp_path):
    """
    Invariant INV-D5.6: Complete closed-loop adaptation shifts weights away from failing modality
    while maintaining probability simplex constraints and system stability.
    """
    prof_mgr = ProfileManager(profiles_dir=tmp_path)
    coordinator = AdaptationCoordinator(profile_manager=prof_mgr, user_id="test_adaptive_user")

    initial_weights = coordinator.get_active_weights()
    assert abs(initial_weights["EYE"] + initial_weights["HEAD"] + initial_weights["HAND"] - 1.0) < 1e-5

    t0 = 1000.0

    # 1. Warm-up: 10 successful interactions -> System should stabilize
    for i in range(10):
        pos_fb = _create_feedback(is_pos=True, conf=0.90)
        metrics, dec, pol, w = coordinator.process_feedback_event(
            feedback=pos_fb,
            weights_snapshot=initial_weights,
            ambient_lux=50.0,
            current_time=t0 + (i * 1.0)
        )
        assert abs(w["EYE"] + w["HEAD"] + w["HAND"] - 1.0) < 1e-5

    assert metrics.interactions_count == 10
    assert metrics.health_state in (SystemHealthState.STABLE, SystemHealthState.IMPROVING, SystemHealthState.LEARNING)

    # 2. Disturbance: 5 consecutive negative feedback events (WRONG_TARGET: gaze failing)
    approved_updates = 0
    for i in range(5):
        neg_fb = _create_feedback(is_pos=False, mode=FailureMode.WRONG_TARGET, conf=0.92)
        metrics, dec, pol, w = coordinator.process_feedback_event(
            feedback=neg_fb,
            weights_snapshot=w,
            ambient_lux=50.0,
            current_time=t0 + 10.0 + (i * 1.0)
        )
        # Check simplex constraint on every iteration
        assert abs(w["EYE"] + w["HEAD"] + w["HAND"] - 1.0) < 1e-5
        assert min(w["EYE"], w["HEAD"], w["HAND"]) >= 0.05
        if dec.verdict == GatekeeperVerdict.APPROVE:
            approved_updates += 1

    # At least one micro-adaptation update must have been approved and applied
    assert approved_updates >= 1

    final_weights = coordinator.get_active_weights()
    # EYE weight must have decreased due to repeated WRONG_TARGET feedback
    assert final_weights["EYE"] < initial_weights["EYE"]
    # HEAD or HAND weights must have compensated
    assert (final_weights["HEAD"] > initial_weights["HEAD"]) or (final_weights["HAND"] > initial_weights["HAND"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

