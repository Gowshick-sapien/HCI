"""
Performance latency benchmark for Research Dashboard event ingestion (Deliverable E3).
Verifies Invariant INV-E3.1: Asynchronous event push latency < 100 ms on CPU.
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication

from src.storage.schemas import (
    ActionContext,
    ActionTier,
    AssessmentMetrics,
    FailureMode,
    FailureSeverity,
    FeedbackEvent,
    FeedbackType,
    GatekeeperDecision,
    GatekeeperVerdict,
    SystemHealthState,
)
from src.ui.research_dashboard import ResearchDashboardWindow


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_dashboard_event_push_latency_budget(qapp):
    """
    Invariant INV-E3.1: Verifies that mean event ingestion latency is < 100 ms on CPU.
    """
    window = ResearchDashboardWindow()

    action = ActionContext(
        action_id="act_bench_01",
        action_name="PRIMARY_CLICK",
        tier=ActionTier.TIER_1_IMMEDIATE,
        timestamp_t0=time.time(),
        target_pid=1234,
        target_window_title="Bench Target",
        feature_snapshot=None,
        weights_snapshot={"EYE": 0.40, "HEAD": 0.30, "HAND": 0.30},
        fused_score=0.88,
        threshold=0.70,
        is_executed=True
    )

    fb = FeedbackEvent(
        feedback_id="fb_bench_01",
        action_id="act_bench_01",
        timestamp=time.time(),
        latency_delta_t=0.45,
        feedback_type=FeedbackType.IMPLICIT_NEG,
        confidence_cfb=0.85,
        failure_mode=FailureMode.USER_OVERRIDE,
        severity=FailureSeverity.SEV_2_MINOR,
        detector_source="IMPLICIT_MOUSE_TAKEOVER"
    )

    decision = GatekeeperDecision(
        verdict=GatekeeperVerdict.APPROVE,
        rejection_reason=None,
        sample_count=4,
        confidence_cfb=0.85,
        sprt_score=2.95,
        effective_learning_rate_scale=1.0
    )

    latencies_ms = []
    n_iterations = 1000

    # Warm-up
    for _ in range(20):
        window.push_action_event(action)
        window.push_feedback_event(fb, decision, sprt_score=2.95)

    # Benchmark loop
    for _ in range(n_iterations):
        t0 = time.perf_counter()
        window.push_action_event(action)
        window.push_feedback_event(fb, decision, sprt_score=2.95)
        dt = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(dt)

    mean_lat = float(np.mean(latencies_ms))
    p95_lat = float(np.percentile(latencies_ms, 95))
    p99_lat = float(np.percentile(latencies_ms, 99))

    print(f"\n[Deliverable E3 Dashboard Ingestion Latency] Mean: {mean_lat:.4f} ms | p95: {p95_lat:.4f} ms | p99: {p99_lat:.4f} ms")

    assert mean_lat < 100.0, f"Mean dashboard ingestion latency {mean_lat:.4f} ms exceeds budget of 100 ms"
    assert p95_lat < 100.0, f"p95 latency {p95_lat:.4f} ms exceeds budget"

    window.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
