"""
Unit tests for Engine 5A: Runtime Performance Assessment Engine.
Verifies Invariant INV-D5.1.
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import numpy as np
import pytest

from src.adaptation.assessment_engine import AssessmentEngine
from src.storage.schemas import (
    AssessmentMetrics,
    FailureMode,
    FailureSeverity,
    FeedbackEvent,
    FeedbackType,
    SystemHealthState,
)


def _make_feedback(is_pos: bool, delta_t: float = 2.0, conf: float = 0.85) -> FeedbackEvent:
    return FeedbackEvent(
        feedback_id="test_fb_001",
        action_id="cmd_001",
        timestamp=time.time(),
        latency_delta_t=delta_t,
        feedback_type=FeedbackType.IMPLICIT_POS if is_pos else FeedbackType.IMPLICIT_NEG,
        confidence_cfb=conf,
        failure_mode=FailureMode.NONE if is_pos else FailureMode.USER_OVERRIDE,
        severity=FailureSeverity.SEV_1_BENIGN if is_pos else FailureSeverity.SEV_2_MINOR,
        detector_source="TEST_DETECTOR"
    )


def test_assessment_engine_bootstrapping_state():
    """Invariant INV-D5.1: Emits BOOTSTRAPPING state when sample count < min_bootstrap_samples."""
    engine = AssessmentEngine(window_size=20, min_bootstrap_samples=8)

    for i in range(5):
        fb = _make_feedback(is_pos=True)
        metrics = engine.record_interaction(fb, weights_snapshot={"EYE": 0.4, "HEAD": 0.3, "HAND": 0.3})

    assert metrics.health_state == SystemHealthState.BOOTSTRAPPING
    assert metrics.interactions_count == 5
    assert 0.0 <= metrics.weight_stability_index <= 1.0
    assert not np.isnan(metrics.expected_calibration_error)


def test_assessment_engine_metrics_calculation():
    """Invariant INV-D5.1: Accurately computes EWMA gain, velocity, ECE, and stability index."""
    engine = AssessmentEngine(window_size=30, min_bootstrap_samples=5)
    t0 = 1000.0

    # Feed 15 successful interactions with stable weights
    for i in range(15):
        fb = _make_feedback(is_pos=True, conf=0.90)
        metrics = engine.record_interaction(
            fb,
            weights_snapshot={"EYE": 0.40, "HEAD": 0.30, "HAND": 0.30},
            interaction_confidence=0.90,
            timestamp=t0 + (i * 1.0)
        )

    assert metrics.health_state == SystemHealthState.STABLE
    assert metrics.weight_stability_index >= 0.80
    assert metrics.interactions_count == 15
    assert metrics.expected_calibration_error < 0.15

    # Feed 5 failures with shifting weights (simulating drift / learning)
    for i in range(5):
        fb = _make_feedback(is_pos=False, conf=0.90)
        metrics = engine.record_interaction(
            fb,
            weights_snapshot={"EYE": 0.20 + (i * 0.05), "HEAD": 0.40, "HAND": 0.40 - (i * 0.05)},
            interaction_confidence=0.90,
            timestamp=t0 + 15.0 + (i * 1.0)
        )

    assert metrics.learning_velocity > 0.0
    assert metrics.health_state in (SystemHealthState.DRIFTING, SystemHealthState.LEARNING)


def test_assessment_engine_reset():
    """Verifies that reset clears buffers and returns to initial state."""
    engine = AssessmentEngine()
    for _ in range(10):
        engine.record_interaction(_make_feedback(True))

    assert engine.compute_metrics().interactions_count == 10
    engine.reset()
    clean_metrics = engine.compute_metrics()
    assert clean_metrics.interactions_count == 0
    assert clean_metrics.health_state == SystemHealthState.BOOTSTRAPPING


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

