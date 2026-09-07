"""
Standalone Launcher for Empirical Research Dashboard & Diagnostics Suite (Deliverable E3).
Integrates live webcam capture, FaceMesh & hand tracking, multimodal fusion, supervisory feedback,
and dual-scale dynamic adaptation into a unified PySide6 empirical research workstation.
Employs non-blocking worker threads and main-thread Qt event dispatching to ensure zero freezing.

Usage:
    python scripts/launch_research_dashboard.py
    python scripts/launch_research_dashboard.py --camera 0
    python scripts/launch_research_dashboard.py --simulated
"""

from __future__ import annotations

import argparse
import collections
import os
import signal
import sys
import threading
import time
import traceback
from pathlib import Path
from typing import Deque, Dict, List, Optional, Tuple

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np
from PySide6.QtCore import QTimer
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from src.adaptation.coordinator import AdaptationCoordinator
from src.capture.frame_types import CameraConfig, RawFrame
from src.capture.video_stream import VideoStream
from src.feedback.observer import FeedbackObserver
from src.feedback.telemetry_logger import FeedbackTelemetryLogger
from src.fusion.command_composer import CommandComposer
from src.gesture.gesture_classifier import GestureClassifier
from src.gesture.modality_arbiter import ModalityArbiter
from src.perception.feature_pipeline import FeaturePipeline
from src.storage.profile_manager import ProfileManager
from src.storage.schemas import (
    ActionContext,
    ActionTier,
    ActionType,
    AssessmentMetrics,
    ComposedCommand,
    DeviceMode,
    FeedbackEvent,
    GatekeeperDecision,
    GatekeeperVerdict,
    PerceptionFrame,
    SystemHealthState,
)
from src.ui.research_dashboard import ResearchDashboardWindow

# Hand landmark skeletal connections (21 landmarks)
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (0, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (0, 13), (13, 14), (14, 15), (15, 16), # Ring
    (0, 17), (17, 18), (18, 19), (19, 20), # Pinky
    (5, 9), (9, 13), (13, 17)              # Palm knuckle base
]


class LiveDashboardWorker(threading.Thread):
    """
    Dedicated background worker thread running video capture, ML perception,
    multimodal fusion, supervisory feedback, and adaptation.
    Communicates with the GUI via thread-safe queues with zero cross-thread blocking.
    """

    def __init__(self, window: ResearchDashboardWindow, camera_id: int = 0) -> None:
        super().__init__(daemon=True, name="LiveDashboardWorkerThread")
        self.window = window
        self.camera_id = camera_id
        self._running = False

        self.telemetry_logger = FeedbackTelemetryLogger()
        self.feedback_observer = FeedbackObserver(telemetry_logger=self.telemetry_logger)
        self.coordinator = AdaptationCoordinator(user_id="default_user")

        def on_feedback_received(event: FeedbackEvent):
            metrics, dec, pol, w = self.coordinator.process_feedback_event(
                feedback=event,
                ambient_lux=50.0
            )
            self.window.push_feedback_event(event, verdict=dec, sprt_score=dec.sprt_score)
            self.window.push_metrics_update(metrics, weights=w)
            print(f"[FEEDBACK] {event.feedback_type.value} | {event.detector_source} -> {event.failure_mode.value} (dt: {event.latency_delta_t:.2f}s) | Gatekeeper: {dec.verdict.value} | Health: {metrics.health_state.value} | Weights: [EYE:{w['EYE']:.2f}, HEAD:{w['HEAD']:.2f}, HAND:{w['HAND']:.2f}]")

        self.feedback_observer.register_feedback_listener(on_feedback_received)

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        self._running = True
        config = CameraConfig(camera_id=self.camera_id, frame_width=640, frame_height=480, target_fps=30)
        stream = VideoStream(config)

        if not stream.start():
            print(f"WARNING: Could not open camera ID {self.camera_id}.")
            return

        pipeline = FeaturePipeline(camera_fov_degrees=60.0, screen_width=1920, screen_height=1080)
        classifier = GestureClassifier()
        arbiter = ModalityArbiter(enable_pynput_hooks=False)
        composer = CommandComposer()
        profile_mgr = ProfileManager()
        profile = profile_mgr.load_profile("default_user")

        last_executed_cmd: Optional[ComposedCommand] = None

        print("[LIVE STREAM ACTIVE] Camera streaming and multimodal analysis running smoothly...")

        while self._running:
            try:
                raw_frame = stream.read_latest_frame(wait_timeout_sec=0.05)
                if raw_frame is None or raw_frame.image is None:
                    time.sleep(0.005)
                    continue

                # 1. Perception
                perc_frame = pipeline.process_frame(raw_frame, profile=profile)

                # 2. Gesture Classification
                gesture_out = classifier.classify(perc_frame.hand, timestamp_ms=perc_frame.timestamp_ms)

                # 3. Modality Arbiter
                arb_gesture, active_mode = arbiter.arbitrate(gesture_out, timestamp_ms=perc_frame.timestamp_ms)

                # 4. Command Composition
                composed_cmd = composer.compose(perc_frame, arb_gesture, profile=profile)

                # Action registration
                if composed_cmd.action_type != ActionType.NO_ACTION and (last_executed_cmd is None or last_executed_cmd.action_type != composed_cmd.action_type):
                    current_w = self.coordinator.get_active_weights()
                    action_ctx = ActionContext(
                        action_id=composed_cmd.action_id,
                        action_name=composed_cmd.action_type.value,
                        tier=ActionTier.TIER_1_IMMEDIATE,
                        timestamp_t0=time.time(),
                        target_pid=os.getpid(),
                        target_window_title="Research Dashboard",
                        feature_snapshot=perc_frame,
                        weights_snapshot=current_w,
                        fused_score=composed_cmd.composed_score,
                        threshold=0.70,
                        is_executed=True
                    )
                    self.feedback_observer.on_action_executed(action_ctx)
                    self.window.push_action_event(action_ctx)
                    last_executed_cmd = composed_cmd
                elif composed_cmd.action_type == ActionType.NO_ACTION:
                    last_executed_cmd = None

                self.feedback_observer.process_perception_frame(perc_frame)
                metrics = self.coordinator.get_latest_metrics()
                weights = self.coordinator.get_active_weights()

                # Push periodic metrics update
                self.window.push_metrics_update(metrics, weights=weights)

                # 5. Annotate Video Frame
                annotated_bgr = raw_frame.image.copy()
                h_img, w_img = annotated_bgr.shape[:2]

                # Draw Hand Skeleton
                if perc_frame.hand.is_detected and perc_frame.hand.raw_landmarks_21:
                    pts = perc_frame.hand.raw_landmarks_21
                    if len(pts) == 21:
                        for p1, p2 in HAND_CONNECTIONS:
                            pt1 = (int(pts[p1][0]), int(pts[p1][1]))
                            pt2 = (int(pts[p2][0]), int(pts[p2][1]))
                            cv2.line(annotated_bgr, pt1, pt2, (0, 255, 128), 2)
                        for idx, pt in enumerate(pts):
                            color = (0, 0, 255) if idx in (4, 8, 12, 16, 20) else (255, 255, 0)
                            cv2.circle(annotated_bgr, (int(pt[0]), int(pt[1])), 4, color, -1)

                # Draw Irises
                if perc_frame.eye.confidence > 0.0:
                    lx, ly = int(perc_frame.eye.left_iris_center[0]), int(perc_frame.eye.left_iris_center[1])
                    rx, ry = int(perc_frame.eye.right_iris_center[0]), int(perc_frame.eye.right_iris_center[1])
                    cv2.circle(annotated_bgr, (lx, ly), 3, (0, 255, 255), -1)
                    cv2.circle(annotated_bgr, (rx, ry), 3, (0, 255, 255), -1)

                # Draw Gaze Reticle & Anchor
                if perc_frame.gaze_screen_xy != (0.0, 0.0):
                    gu, gv = perc_frame.gaze_screen_xy
                    gx = int(np.clip((gu / 1920.0) * w_img, 10, w_img - 10))
                    gy = int(np.clip((gv / 1080.0) * h_img, 10, h_img - 10))
                    cv2.circle(annotated_bgr, (gx, gy), 10, (0, 255, 0), 1)
                    cv2.drawMarker(annotated_bgr, (gx, gy), (0, 255, 0), cv2.MARKER_CROSS, 16, 1)

                    if perc_frame.gaze_anchor is not None:
                        ax = int(np.clip((perc_frame.gaze_anchor[0] / 1920.0) * w_img, 20, w_img - 20))
                        ay = int(np.clip((perc_frame.gaze_anchor[1] / 1080.0) * h_img, 20, h_img - 20))
                        cv2.circle(annotated_bgr, (ax, ay), 16, (255, 255, 0), 2)
                        cv2.drawMarker(annotated_bgr, (ax, ay), (255, 255, 0), cv2.MARKER_CROSS, 24, 2)
                        cv2.putText(annotated_bgr, "ANCHOR [LOCKED]", (ax + 12, ay - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)

                # Convert to QImage and push to GUI video widget
                rgb_arr = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_arr.shape
                bytes_per_line = ch * w
                qimg = QImage(rgb_arr.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()
                self.window.push_video_frame(qimg)

            except Exception as e:
                time.sleep(0.01)

        stream.stop()
        pipeline.close()


def main():
    parser = argparse.ArgumentParser(description="Deliverable E3 Empirical Research Dashboard")
    parser.add_argument("--camera", type=int, default=0, help="Camera device index (default: 0)")
    parser.add_argument("--simulated", action="store_true", help="Run without live webcam")
    args = parser.parse_args()

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    print("================================================================================")
    print("  DELIVERABLE E3: EMPIRICAL RESEARCH DASHBOARD & DIAGNOSTICS SUITE")
    print("================================================================================")
    print(f"Connecting Camera Device ID: {args.camera}")
    print("Initializing Multi-Tab Research Dashboard...")
    print("Tabs: [1. Telemetry] [2. Parameter Trajectory] [3. SPRT Monitor] [4. Study Runner] [5. Reports]\n")

    window = ResearchDashboardWindow()
    window.show()

    worker = None
    if not args.simulated:
        worker = LiveDashboardWorker(window, camera_id=args.camera)
        worker.start()

    sigint_timer = QTimer()
    sigint_timer.timeout.connect(lambda: None)
    sigint_timer.start(200)

    try:
        sys.exit(app.exec())
    finally:
        if worker is not None:
            worker.stop()


if __name__ == "__main__":
    main()
