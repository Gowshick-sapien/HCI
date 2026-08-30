"""
Micro-benchmark for Stage 3A Command Composer and Simplex Projection.
Verifies Invariant INV-D2.5: Execution latency <= 1.0 ms.
"""

import time
import numpy as np
import pytest

from src.fusion.command_composer import CommandComposer
from src.fusion.simplex_projection import SimplexProjectionEngine
from src.storage.schemas import (
    EyeLandmarks,
    GestureClassification,
    GestureToken,
    HandLandmarks,
    HeadPoseLandmarks,
    PerceptionFrame,
    ProfileSnapshot,
)


def test_fusion_and_simplex_latency():
    """Invariant INV-D2.5: Stage 3A Command Composer + Simplex Projection latency <= 1.0 ms."""
    composer = CommandComposer()
    profile = ProfileSnapshot.create_default()

    eye = EyeLandmarks(left_iris_center=(300.0, 400.0), right_iris_center=(370.0, 400.0), left_ear=0.28, right_ear=0.28, iris_ratio_x=0.5, iris_ratio_y=0.5, confidence=0.90)
    head = HeadPoseLandmarks(yaw=0.0, pitch=0.0, roll=0.0, translation_vector=(0, 0, 0), mahalanobis_distance=0.5, confidence=0.95)
    hand = HandLandmarks(is_detected=True, pinch_distance=0.02, palm_normal=(0, 0, 1), wrist_position=(0.5, 0.5, 0), wrist_velocity=0.1, gesture_class="PINCH", confidence=0.90)
    perc = PerceptionFrame(frame_id=1, timestamp_ms=1000.0, eye=eye, head=head, hand=hand, gaze_confidence=0.90, head_confidence=0.95, gaze_screen_xy=(960.0, 540.0), head_euler_angles=(0, 0, 0), gaze_dwell_ms=150.0, gaze_stability=1.0, gaze_anchor=(800.0, 450.0))
    gesture = GestureClassification(gesture_token=GestureToken.PINCH_INDEX, c_gesture=0.88, requires_gaze_target=True, action_intent="PRIMARY_CLICK", stable_duration_ms=100.0, timestamp_ms=1000.0)

    # Warm-up (100 iterations)
    for _ in range(100):
        _ = composer.compose(perc, gesture, profile=profile)
        _ = SimplexProjectionEngine.project_simplex_1d([0.4, 0.2, 0.4])

    num_iterations = 1000
    latencies_ms = []

    for _ in range(num_iterations):
        t0 = time.perf_counter()
        _ = composer.compose(perc, gesture, profile=profile)
        _ = SimplexProjectionEngine.project_simplex_1d([0.4, 0.2, 0.4])
        elapsed = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(elapsed)

    mean_lat = float(np.mean(latencies_ms))
    p95_lat = float(np.percentile(latencies_ms, 95))

    print(f"\n[BENCHMARK] Stage 3A Command Composer & Simplex Mean Latency: {mean_lat:.4f} ms (p95: {p95_lat:.4f} ms)")

    # Assert invariant: <= 1.0 ms
    assert mean_lat <= 1.0, f"Mean latency {mean_lat:.4f} ms exceeded 1.0 ms threshold"
