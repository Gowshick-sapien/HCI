"""
Performance latency benchmark for Layer 5 Dual-Scale Dynamic Adaptation.
Verifies Invariant INV-D5.5: Total closed-loop evaluation cycle <= 2.0 ms on CPU.
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
)


def test_adaptation_latency_budget(tmp_path):
    """
    Invariant INV-D5.5: Benchmark verifying mean closed-loop evaluation latency <= 2.0 ms.
    """
    prof_mgr = ProfileManager(profiles_dir=tmp_path)
    coordinator = AdaptationCoordinator(profile_manager=prof_mgr, user_id="bench_user")

    fb_event = FeedbackEvent(
        feedback_id="bench_fb_01",
        action_id="cmd_bench_01",
        timestamp=time.time(),
        latency_delta_t=0.50,
        feedback_type=FeedbackType.IMPLICIT_NEG,
        confidence_cfb=0.88,
        failure_mode=FailureMode.USER_OVERRIDE,
        severity=FailureSeverity.SEV_2_MINOR,
        detector_source="BENCHMARK_DETECTOR"
    )

    latencies_ms = []
    n_iterations = 1000

    # Warm-up
    for _ in range(50):
        coordinator.process_feedback_event(fb_event, ambient_lux=50.0)

    # Benchmark loop
    for i in range(n_iterations):
        t0 = time.perf_counter()
        coordinator.process_feedback_event(fb_event, ambient_lux=50.0)
        dt = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(dt)

    mean_latency = float(np.mean(latencies_ms))
    p95_latency = float(np.percentile(latencies_ms, 95))
    p99_latency = float(np.percentile(latencies_ms, 99))

    print(f"\n[Layer 5 Adaptation Latency Benchmark] Mean: {mean_latency:.4f} ms | p95: {p95_latency:.4f} ms | p99: {p99_latency:.4f} ms")

    assert mean_latency <= 2.00, f"Mean latency {mean_latency:.4f} ms exceeds budget of 2.0 ms"
    assert p95_latency <= 4.00, f"p95 latency {p95_latency:.4f} ms exceeds 4.0 ms threshold"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

