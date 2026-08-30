"""
Unit tests for Engine 5C: Macro-Adaptation Policy State Machine.
Verifies Invariant INV-D5.4.
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest

from src.adaptation.macro_adaptation import MacroAdaptationEngine
from src.storage.schemas import (
    AssessmentMetrics,
    MacroPolicy,
    SystemHealthState,
)


def _make_metrics(
    health: SystemHealthState = SystemHealthState.STABLE,
    stability: float = 0.90,
    count: int = 20,
    ece: float = 0.05,
    gain: float = 0.05
) -> AssessmentMetrics:
    return AssessmentMetrics(
        timestamp=time.time(),
        interactions_count=count,
        adaptation_gain_ewma=gain,
        learning_velocity=0.01,
        weight_stability_index=stability,
        adaptation_confidence_index=0.85,
        expected_calibration_error=ece,
        recovery_rate=1.0,
        drift_recovery_time=0.0,
        health_state=health
    )


def test_macro_adaptation_freeze_on_low_light():
    """Invariant INV-D5.4: Evaluates FREEZE policy under low ambient illuminance."""
    engine = MacroAdaptationEngine(min_ambient_lux_freeze=15.0)

    # 1. Normal metrics, but low light (10 lux < 15 lux) -> FREEZE
    metrics_normal = _make_metrics(health=SystemHealthState.STABLE)
    policy = engine.evaluate_policy(metrics_normal, ambient_lux=10.0)
    assert policy == MacroPolicy.FREEZE

    # 2. Good light (50 lux >= 15 lux) with DRIFTING health -> MERGE (allows active micro-adaptation recovery)
    metrics_drifting = _make_metrics(health=SystemHealthState.DRIFTING)
    policy = engine.evaluate_policy(metrics_drifting, ambient_lux=50.0)
    assert policy == MacroPolicy.MERGE


def test_macro_adaptation_recalibrate_trigger():
    """Invariant INV-D5.4: Triggers RECALIBRATE when ECE exceeds threshold after sufficient interactions."""
    engine = MacroAdaptationEngine(recalibrate_ece_threshold=0.25, merge_min_interactions=10)
    metrics_bad_calib = _make_metrics(health=SystemHealthState.LEARNING, count=15, ece=0.32)

    policy = engine.evaluate_policy(metrics_bad_calib, ambient_lux=50.0)
    assert policy == MacroPolicy.RECALIBRATE


def test_macro_adaptation_merge_execution():
    """Invariant INV-D5.4: Executes MERGE blending baseline and session weights correctly."""
    engine = MacroAdaptationEngine(merge_blend_factor=0.50)

    baseline = {"EYE": 0.50, "HEAD": 0.25, "HAND": 0.25}
    session = {"EYE": 0.30, "HEAD": 0.35, "HAND": 0.35}

    merged = engine.execute_merge(baseline, session)

    # Expected blended: EYE = 0.5*0.5 + 0.5*0.3 = 0.40, HEAD = 0.5*0.25 + 0.5*0.35 = 0.30, HAND = 0.30
    assert abs(merged["EYE"] - 0.40) < 1e-4
    assert abs(merged["HEAD"] - 0.30) < 1e-4
    assert abs(merged["HAND"] - 0.30) < 1e-4
    assert abs(merged["EYE"] + merged["HEAD"] + merged["HAND"] - 1.0) < 1e-5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

