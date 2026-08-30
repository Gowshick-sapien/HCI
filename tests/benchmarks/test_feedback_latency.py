"""
Latency and Performance Micro-Benchmark for Deliverable D4.
Verifies Invariant INV-D4.6: Total Layer 4 evaluation cycle latency <= 1.5 ms on CPU.
"""

import time
import numpy as np
import pytest

from src.feedback.observer import FeedbackObserver
from src.storage.schemas import (
    ActionContext,
    ActionTier,
    HeadPoseLandmarks,
    PerceptionFrame,
)


def test_feedback_observer_latency_budget():
    """Invariant INV-D4.6: Total Layer 4 evaluation cycle latency <= 1.5 ms on CPU."""
    observer = FeedbackObserver()

    # Pre-generate mock perception frame with head pose
    mock_head = HeadPoseLandmarks(
        yaw=5.0, pitch=-2.0, roll=0.0,
        translation_vector=(0.0, 0.0, 500.0),
        mahalanobis_distance=0.0, confidence=1.0
    )

    t0 = 1000.0
    action = ActionContext(
        action_id="act_bench_001",
        action_name="PRIMARY_CLICK",
        tier=ActionTier.TIER_1_IMMEDIATE,
        timestamp_t0=t0,
        target_pid=1111,
        target_window_title="Bench Window",
        feature_snapshot=None,
        weights_snapshot={"GAZE": 0.5, "GESTURE": 0.5},
        fused_score=0.85,
        threshold=0.70,
        is_executed=True
    )
    observer.on_action_executed(action)

    latencies_us = []
    num_cycles = 1000

    for i in range(num_cycles):
        now = t0 + 0.50 + i * 0.001

        t_start = time.perf_counter_ns()
        # 1. Update explicit head kinematics
        observer.explicit_classifier.update(head_pose=mock_head, timestamp_sec=now, action=action)
        # 2. Check mouse takeover
        observer.implicit_detector.evaluate_mouse_takeover(action=action, mouse_dx=2.0, mouse_dy=1.0, current_time=now)
        # 3. Check stability expirations
        observer.correlator.check_stability_expirations(current_time=now)
        elapsed_us = (time.perf_counter_ns() - t_start) / 1000.0
        latencies_us.append(elapsed_us)

    mean_latency_ms = float(np.mean(latencies_us)) / 1000.0
    p95_latency_ms = float(np.percentile(latencies_us, 95)) / 1000.0

    print(f"\n[BENCHMARK] Layer 4 Feedback Observer Mean Latency: {mean_latency_ms:.4f} ms (p95: {p95_latency_ms:.4f} ms)")

    # Invariant threshold check: mean latency <= 1.5 ms
    assert mean_latency_ms <= 1.5, f"Mean latency {mean_latency_ms:.4f} ms exceeded budget of 1.5 ms"
