"""
Latency and Performance Benchmarks for Deliverable D1.
Verifies Invariant INV-D1.1: Total perception cycle <= 20.5 ms per frame.
"""

import time
import numpy as np
import pytest

from src.capture.frame_types import RawFrame
from src.gesture.gesture_classifier import GestureClassifier
from src.gesture.modality_arbiter import ModalityArbiter
from src.perception.feature_pipeline import FeaturePipeline
from src.storage.schemas import ProfileSnapshot


def test_frame_latency_budget():
    """Invariant INV-D1.1: Total Layer 1 + Layer 1B + Arbiter latency <= 20.5 ms."""
    pipeline = FeaturePipeline(screen_width=1920, screen_height=1080)
    classifier = GestureClassifier()
    arbiter = ModalityArbiter(enable_pynput_hooks=False)
    profile = ProfileSnapshot.create_default()

    # Pre-generate synthetic frames
    num_frames = 50
    dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Warm-up run (10 frames) to let JIT/models initialize
    for i in range(10):
        rf = RawFrame(frame_id=i, timestamp=time.time(), width=640, height=480, ambient_lux=50.0, capture_latency_ms=1.0, image=dummy_img)
        pf = pipeline.process_frame(rf, profile)
        g = classifier.classify(pf.hand, pf.timestamp_ms)
        arbiter.arbitrate(g, pf.timestamp_ms)

    latencies = []
    for i in range(num_frames):
        t0 = time.perf_counter()
        rf = RawFrame(frame_id=i, timestamp=time.time(), width=640, height=480, ambient_lux=50.0, capture_latency_ms=1.0, image=dummy_img)
        pf = pipeline.process_frame(rf, profile)
        g = classifier.classify(pf.hand, pf.timestamp_ms)
        arbiter.arbitrate(g, pf.timestamp_ms)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(elapsed_ms)

    pipeline.close()

    mean_latency = float(np.mean(latencies))
    p95_latency = float(np.percentile(latencies, 95))
    
    print(f"\n[BENCHMARK] Deliverable D1 Mean Latency: {mean_latency:.2f} ms (p95: {p95_latency:.2f} ms)")
    
    # Invariant threshold check: mean latency <= 20.5 ms
    assert mean_latency <= 20.5, f"Mean latency {mean_latency:.2f} ms exceeded budget of 20.5 ms"
