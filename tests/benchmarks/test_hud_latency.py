"""
Performance latency benchmark for Explainability HUD Overlay (Deliverable E2).
Verifies Invariant INV-E2.1: HUD paint event executes in <= 1.0 ms on CPU.
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import numpy as np
import pytest
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from src.storage.schemas import (
    ActionType,
    AssessmentMetrics,
    ComposedCommand,
    DeviceMode,
    EyeLandmarks,
    GestureToken,
    HandLandmarks,
    HeadPoseLandmarks,
    PerceptionFrame,
    SystemHealthState,
)
from src.ui.explainability_hud import ExplainabilityHUDOverlay


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_hud_paint_latency_budget(qapp):
    """
    Invariant INV-E2.1: Benchmark verifying mean paint execution time <= 1.0 ms on CPU.
    """
    hud = ExplainabilityHUDOverlay(screen_width=1920, screen_height=1080)

    perc_frame = PerceptionFrame(
        timestamp_ms=1000.0,
        frame_id=1,
        eye=EyeLandmarks((320.0, 240.0), (340.0, 240.0), 0.28, 0.28, 0.5, 0.5, 0.85),
        head=HeadPoseLandmarks(0.0, 0.0, 0.0, (0.0, 0.0, 0.0), 0.1, 0.90),
        hand=HandLandmarks(True, 0.02, (0.0, 0.0, 1.0), (640.0, 480.0, 0.0), 0.0, "PINCH_INDEX", 0.88),
        gaze_confidence=0.85,
        head_confidence=0.90,
        gaze_screen_xy=(960.0, 540.0),
        head_euler_angles=(0.0, 0.0, 0.0),
        gaze_dwell_ms=450.0,
        gaze_stability=0.92,
        gaze_anchor=(960.0, 540.0)
    )

    metrics = AssessmentMetrics(
        timestamp=time.time(),
        interactions_count=25,
        adaptation_gain_ewma=0.06,
        learning_velocity=0.01,
        weight_stability_index=0.90,
        adaptation_confidence_index=0.88,
        expected_calibration_error=0.04,
        recovery_rate=1.0,
        drift_recovery_time=0.0,
        health_state=SystemHealthState.STABLE
    )

    command = ComposedCommand(
        action_id="cmd_bench_01",
        action_type=ActionType.PRIMARY_CLICK,
        gaze_anchor=(960.0, 540.0),
        gesture_token=GestureToken.PINCH_INDEX,
        c_target=0.85,
        c_gesture=0.88,
        composed_score=0.88,
        requires_gaze_target=True,
        timestamp_ms=1000.0
    )

    hud.update_telemetry(
        perception=perc_frame,
        command=command,
        metrics=metrics,
        device_mode=DeviceMode.GESTURE,
        weights={"EYE": 0.40, "HEAD": 0.30, "HAND": 0.30}
    )

    latencies_ms = []
    n_iterations = 1000

    # Off-screen test canvas image for direct QPainter benchmarking
    test_canvas = QImage(1920, 1080, QImage.Format.Format_ARGB32_Premultiplied)

    # Warm-up
    for _ in range(50):
        painter = QPainter(test_canvas)
        hud._draw_health_status_card(painter, metrics, DeviceMode.GESTURE)
        hud._draw_confidence_breakdown_card(painter, perc_frame, {"EYE": 0.4, "HEAD": 0.3, "HAND": 0.3}, command)
        hud._draw_spatial_gaze_and_dwell(painter, perc_frame, command)
        painter.end()

    # Benchmark loop
    for _ in range(n_iterations):
        t0 = time.perf_counter()
        painter = QPainter(test_canvas)
        hud._draw_health_status_card(painter, metrics, DeviceMode.GESTURE)
        hud._draw_confidence_breakdown_card(painter, perc_frame, {"EYE": 0.4, "HEAD": 0.3, "HAND": 0.3}, command)
        hud._draw_spatial_gaze_and_dwell(painter, perc_frame, command)
        painter.end()
        dt = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(dt)

    mean_lat = float(np.mean(latencies_ms))
    p95_lat = float(np.percentile(latencies_ms, 95))
    p99_lat = float(np.percentile(latencies_ms, 99))

    print(f"\n[Deliverable E2 HUD Paint Latency Benchmark] Mean: {mean_lat:.4f} ms | p95: {p95_lat:.4f} ms | p99: {p99_lat:.4f} ms")

    assert mean_lat <= 1.00, f"Mean HUD paint latency {mean_lat:.4f} ms exceeds budget of 1.0 ms"
    assert p95_lat <= 2.50, f"p95 latency {p95_lat:.4f} ms exceeds threshold"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
