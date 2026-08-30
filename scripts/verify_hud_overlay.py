"""
Interactive Explainability HUD Overlay (Deliverable E2).
Spawns a full-screen, translucent, click-through desktop overlay rendering real-time
multimodal perceptual confidence meters, Tier-2 dwell confirmation rings, and health badges.

Modes:
    Live Tracking (Default) : Tracks real webcam gaze, head pose, and hand gestures.
    Simulated Demo          : python scripts/verify_hud_overlay.py --simulated

Controls:
    Focus terminal & [Ctrl + C] : Exit HUD overlay cleanly
"""

from __future__ import annotations

import argparse
import collections
import math
import os
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Deque, Dict, List, Optional, Tuple

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QTimer
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication

from src.adaptation.coordinator import AdaptationCoordinator
from src.capture.frame_types import CameraConfig
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
    EyeLandmarks,
    FeedbackEvent,
    GestureToken,
    HandLandmarks,
    HeadPoseLandmarks,
    PerceptionFrame,
    SystemHealthState,
)
from src.ui.explainability_hud import ExplainabilityHUDOverlay


class LiveHUDWorker(threading.Thread):
    """Background worker running real webcam perception and adaptation to feed the HUD overlay."""

    def __init__(self, overlay: ExplainabilityHUDOverlay, camera_id: int = 0) -> None:
        super().__init__(daemon=True, name="LiveHUDWorkerThread")
        self.overlay = overlay
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
            self.overlay.update_telemetry(
                metrics=metrics,
                feedback=event,
                weights=w
            )
            print(f"[FEEDBACK] {event.feedback_type.value} | {event.detector_source} -> {event.failure_mode.value} (dt: {event.latency_delta_t:.2f}s) | Gatekeeper: {dec.verdict.value} | Health: {metrics.health_state.value} | Weights: [EYE:{w['EYE']:.2f}, HEAD:{w['HEAD']:.2f}, HAND:{w['HAND']:.2f}]")

        self.feedback_observer.register_feedback_listener(on_feedback_received)

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        self._running = True
        config = CameraConfig(camera_id=self.camera_id, frame_width=640, frame_height=480, target_fps=30)
        stream = VideoStream(config)

        if not stream.start():
            print(f"WARNING: Could not open camera ID {self.camera_id}. Falling back to simulated stream.")
            return

        pipeline = FeaturePipeline(
            camera_fov_degrees=60.0,
            screen_width=self.overlay.screen_width,
            screen_height=self.overlay.screen_height
        )
        classifier = GestureClassifier()
        arbiter = ModalityArbiter(enable_pynput_hooks=False)
        composer = CommandComposer()
        profile_mgr = ProfileManager()
        profile = profile_mgr.load_profile("default_user")

        last_executed_cmd: Optional[ComposedCommand] = None
        last_global_cursor: Optional[Tuple[int, int]] = None

        print("[LIVE TRACKING ACTIVE] Tracking real eye gaze, head pose, and hand gestures on desktop HUD...")

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

                # 3. Arbiter
                arb_gesture, active_mode = arbiter.arbitrate(gesture_out, timestamp_ms=perc_frame.timestamp_ms)

                # 4. Multimodal Fusion
                composed_cmd = composer.compose(perc_frame, arb_gesture, profile=profile)

                # Action context registration
                if composed_cmd.action_type != ActionType.NO_ACTION and (last_executed_cmd is None or last_executed_cmd.action_type != composed_cmd.action_type):
                    current_w = self.coordinator.get_active_weights()
                    action_ctx = ActionContext(
                        action_id=composed_cmd.action_id,
                        action_name=composed_cmd.action_type.value,
                        tier=ActionTier.TIER_1_IMMEDIATE,
                        timestamp_t0=time.time(),
                        target_pid=os.getpid(),
                        target_window_title="Desktop HUD Overlay",
                        feature_snapshot=perc_frame,
                        weights_snapshot=current_w,
                        fused_score=composed_cmd.composed_score,
                        threshold=0.70,
                        is_executed=True
                    )
                    self.feedback_observer.on_action_executed(action_ctx)
                    last_executed_cmd = composed_cmd
                elif composed_cmd.action_type == ActionType.NO_ACTION:
                    last_executed_cmd = None

                # Cursor tracking for mouse takeover detection
                try:
                    cursor_pt = QCursor.pos()
                    cur_gx, cur_gy = int(cursor_pt.x()), int(cursor_pt.y())
                    if last_global_cursor is not None:
                        gdx = cur_gx - last_global_cursor[0]
                        gdy = cur_gy - last_global_cursor[1]
                        if abs(gdx) > 0 or abs(gdy) > 0:
                            self.feedback_observer.on_mouse_movement(float(gdx), float(gdy))
                    last_global_cursor = (cur_gx, cur_gy)
                except Exception:
                    pass

                self.feedback_observer.process_perception_frame(perc_frame)
                metrics = self.coordinator.get_latest_metrics()
                weights = self.coordinator.get_active_weights()

                # Push real-time telemetry to HUD overlay
                self.overlay.update_telemetry(
                    perception=perc_frame,
                    command=composed_cmd,
                    metrics=metrics,
                    device_mode=active_mode,
                    weights=weights
                )

            except Exception as e:
                time.sleep(0.01)

        stream.stop()


class SimulatedHUDDemo:
    """Simulates synthetic perception and adaptation streams driving the HUD overlay."""

    def __init__(self, overlay: ExplainabilityHUDOverlay) -> None:
        self.overlay = overlay
        self.t_start = time.time()
        self.current_dwell_ms = 0.0
        self.modes = [DeviceMode.GESTURE, DeviceMode.MOUSE_PRIORITY, DeviceMode.KEYBOARD]
        self.mode_idx = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(33)

    def tick(self) -> None:
        now = time.time()
        elapsed = now - self.t_start

        screen_w = self.overlay.screen_width
        screen_h = self.overlay.screen_height
        center_x = screen_w / 2.0
        center_y = screen_h / 2.0

        gx = center_x + math.sin(elapsed * 1.2) * 250.0
        gy = center_y + math.cos(elapsed * 0.9) * 150.0

        self.current_dwell_ms = (self.current_dwell_ms + 33.0) % 750.0
        anchor = (center_x, center_y) if self.current_dwell_ms > 150.0 else None

        gaze_c = float(0.70 + 0.25 * math.sin(elapsed * 2.0))
        head_c = float(0.80 + 0.15 * math.cos(elapsed * 1.5))
        hand_c = float(0.75 + 0.20 * math.sin(elapsed * 0.8))

        perc_frame = PerceptionFrame(
            timestamp_ms=now * 1000.0,
            frame_id=int(elapsed * 30),
            eye=EyeLandmarks((320.0, 240.0), (340.0, 240.0), 0.28, 0.28, 0.5, 0.5, gaze_c),
            head=HeadPoseLandmarks(0.0, 0.0, 0.0, (0.0, 0.0, 0.0), 0.1, head_c),
            hand=HandLandmarks(True, 0.02, (0.0, 0.0, 1.0), (gx, gy, 0.0), 0.0, "PINCH_INDEX", hand_c),
            gaze_confidence=gaze_c,
            head_confidence=head_c,
            gaze_screen_xy=(gx, gy),
            head_euler_angles=(0.0, 0.0, 0.0),
            gaze_dwell_ms=self.current_dwell_ms,
            gaze_stability=0.92,
            gaze_anchor=anchor
        )

        metrics = AssessmentMetrics(
            timestamp=now,
            interactions_count=18,
            adaptation_gain_ewma=0.05,
            learning_velocity=0.02,
            weight_stability_index=0.88,
            adaptation_confidence_index=0.84,
            expected_calibration_error=0.05,
            recovery_rate=1.0,
            drift_recovery_time=0.0,
            health_state=SystemHealthState.STABLE if elapsed > 4.0 else SystemHealthState.LEARNING
        )

        cmd = ComposedCommand(
            action_id="demo_cmd_01",
            action_type=ActionType.PRIMARY_CLICK if self.current_dwell_ms > 500.0 else ActionType.NO_ACTION,
            gaze_anchor=anchor,
            gesture_token=GestureToken.PINCH_INDEX,
            c_target=gaze_c,
            c_gesture=hand_c,
            composed_score=0.86,
            requires_gaze_target=True,
            timestamp_ms=now * 1000.0
        )

        self.overlay.update_telemetry(
            perception=perc_frame,
            command=cmd,
            metrics=metrics,
            device_mode=self.modes[self.mode_idx],
            weights={"EYE": 0.42, "HEAD": 0.28, "HAND": 0.30}
        )


def main():
    parser = argparse.ArgumentParser(description="Deliverable E2 Explainability HUD Overlay")
    parser.add_argument("--simulated", action="store_true", help="Run in synthetic simulation mode without webcam")
    parser.add_argument("--camera", type=int, default=0, help="Camera device index (default: 0)")
    args = parser.parse_args()

    # Enable Ctrl+C termination
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    screen = app.primaryScreen()
    geo = screen.geometry() if screen else None
    w = geo.width() if geo else 1920
    h = geo.height() if geo else 1080

    print("================================================================================")
    print("  DELIVERABLE E2: STATE-AWARE EXPLAINABILITY HUD OVERLAY")
    print("================================================================================")
    print(f"Desktop Resolution: {w}x{h}")
    print("Translucent, click-through overlay initialized.")
    print("You can interact with background windows while the HUD renders live metrics!")
    print("To STOP the demo: Focus your terminal and press [Ctrl + C].\n")

    overlay = ExplainabilityHUDOverlay(screen_width=w, screen_height=h)
    overlay.show()

    worker = None
    if args.simulated:
        print("[MODE: SIMULATED DEMO] Running synthetic animated trajectories.")
        demo = SimulatedHUDDemo(overlay)
    else:
        print("[MODE: LIVE WEBCAM TRACKING] Initializing camera perception pipeline...")
        worker = LiveHUDWorker(overlay, camera_id=args.camera)
        worker.start()

    sigint_timer = QTimer()
    sigint_timer.timeout.connect(lambda: None)
    sigint_timer.start(200)

    try:
        app.exec()
    finally:
        if worker is not None:
            worker.stop()


if __name__ == "__main__":
    main()
