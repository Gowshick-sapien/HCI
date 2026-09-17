#!/usr/bin/env python3
"""
Interactive Multimodal HCI Test Bench Suite Launcher.
Deliverables: TBS-D1 (Frontend) & TBS-D2 (Streaming Bridge & Verification Engine)
Strict Zero Emojis Policy Enforced Across Entire Scope.
"""

from __future__ import annotations

import argparse
import logging
import math
import os
import signal
import sys
import time
from typing import Any, Dict, Optional, Tuple
import uuid
import webbrowser

import numpy as np

# Add project root to Python search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.adaptation.coordinator import AdaptationCoordinator
from src.capture import CameraConfig, VideoStream
from src.feedback.telemetry_logger import FeedbackTelemetryLogger
from src.fusion.command_composer import CommandComposer
from src.gesture.gesture_classifier import GestureClassifier
from src.gesture.modality_arbiter import ModalityArbiter
from src.perception.feature_pipeline import FeaturePipeline
from src.storage.profile_manager import ProfileManager
from src.storage.schemas import (
    ActionType,
    FailureMode,
    FailureSeverity,
    FeedbackEvent,
    FeedbackType,
    GatekeeperVerdict,
    GestureToken,
)
from src.testbench.server import TestbenchServer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("TestbenchLauncher")


def get_screen_dimensions() -> Tuple[int, int]:
    """
    Determines logical desktop display resolution matching the browser viewport.
    Falls back to 1920x1080 if system query fails.
    """
    try:
        import ctypes
        user32 = ctypes.windll.user32
        w = int(user32.GetSystemMetrics(0))
        h = int(user32.GetSystemMetrics(1))
        if w > 0 and h > 0:
            return w, h
    except Exception:
        pass
    return 1920, 1080


class TestbenchRunner:
    """
    Coordinates the execution of the Test Bench Suite.
    Binds the multimodal perception pipeline to the asynchronous web server.
    """

    def __init__(
        self,
        camera_id: int = 0,
        host: str = "127.0.0.1",
        port: int = 8080,
        simulated: bool = False,
        launch_browser: bool = True,
        user_id: str = "default_user",
    ) -> None:
        self.camera_id = camera_id
        self.host = host
        self.port = port
        self.simulated = simulated
        self.launch_browser = launch_browser
        self.user_id = user_id

        self.profile_mgr = ProfileManager()
        self.coordinator = AdaptationCoordinator(profile_manager=self.profile_mgr, user_id=self.user_id)
        self.telemetry_logger = FeedbackTelemetryLogger()

        self.server: Optional[TestbenchServer] = None
        self.stream: Optional[VideoStream] = None
        self._running = False
        self._interaction_count = 0

    def _on_interaction_event(self, event: Dict[str, Any]) -> None:
        """Callback triggered when the browser frontend reports a verified interaction."""
        self._interaction_count += 1
        target_id = event.get("target_id", "UNKNOWN")
        action_type = event.get("action_type", "UNKNOWN")
        is_success = event.get("is_successful", False)
        status_str = "SUCCESS" if is_success else "FAILED"
        print(f"[TESTBENCH EVENT #{self._interaction_count}] Target: {target_id} | Action: {action_type} | Result: {status_str}")

        # Construct strongly-typed supervisory FeedbackEvent
        mv_time = float(event.get("movement_time_ms", 500.0)) / 1000.0
        fb_event = FeedbackEvent(
            feedback_id=f"fb_tb_{uuid.uuid4().hex[:8]}",
            action_id=str(target_id),
            timestamp=time.time(),
            latency_delta_t=mv_time,
            feedback_type=FeedbackType.IMPLICIT_POS if is_success else FeedbackType.IMPLICIT_NEG,
            confidence_cfb=0.90 if is_success else 0.75,
            failure_mode=FailureMode.NONE if is_success else FailureMode.WRONG_TARGET,
            severity=FailureSeverity.SEV_1_BENIGN if is_success else FailureSeverity.SEV_2_MINOR,
            detector_source="TESTBENCH_FRONTEND",
            raw_event_payload=event,
        )

        # 1. Log to logs/feedback_events.jsonl on disk
        self.telemetry_logger.log_event(fb_event)

        # 2. Feed into Layer 5 Closed-Loop Adaptation
        metrics, decision, policy, weights = self.coordinator.process_feedback_event(fb_event)
        if decision.verdict == GatekeeperVerdict.APPROVE:
            print(f"  [ONLINE LEARNING] Gatekeeper APPROVED update. Health: {metrics.health_state.value} | Active Weights: EYE={weights['EYE']:.2f}, HEAD={weights['HEAD']:.2f}, HAND={weights['HAND']:.2f}")

    def run(self) -> None:
        """Main execution loop for the Test Bench Suite."""
        self._running = True

        print("=" * 72)
        print("Multimodal Human-Computer Interaction Test Bench Suite (TBS)")
        print("Deliverables: TBS-D1 (Frontend Interface) & TBS-D2 (Streaming Bridge)")
        print("Strict Zero Emojis Policy Enforced")
        print("=" * 72)

        # 1. Initialize and start the HTTP / WebSocket server
        self.server = TestbenchServer(host=self.host, port=self.port)
        self.server.register_callback(self._on_interaction_event)
        self.server.start(blocking=False)

        url = f"http://{self.host}:{self.port}"
        print(f"Server URL:     {url}")
        print(f"WebSocket URL:  ws://{self.host}:{self.port}/ws")

        # 2. Check camera or fallback to simulated perception mode
        use_simulation = self.simulated

        if not use_simulation:
            print(f"Initializing physical webcam (Camera ID: {self.camera_id})...")
            config = CameraConfig(camera_id=self.camera_id, frame_width=640, frame_height=480, target_fps=30)
            self.stream = VideoStream(config)
            if not self.stream.start():
                print("[WARNING] Could not open physical webcam. Activating synthetic simulation mode.")
                use_simulation = True
                self.stream = None

        if use_simulation:
            print("Perception Pipeline: SYNTHETIC SIMULATION MODE")
            print("Target Trajectory:   Iterating across interactive UI test targets (TB-T01 to TB-T08)")
        else:
            print("Perception Pipeline: LIVE MULTIMODAL CAMERA STREAM")

        print("Hitbox Standards:    All target zones >= 140px width x 60px height")
        print("Press Ctrl+C to terminate testbench session safely.")
        print("=" * 72)

        # 3. Launch Web Browser
        if self.launch_browser:
            time.sleep(0.5)
            print(f"Opening default browser to {url}...")
            webbrowser.open(url)

        # 4. Pipeline Execution
        if use_simulation:
            self._run_simulation_loop()
        else:
            self._run_live_loop()

    def _run_simulation_loop(self) -> None:
        """Generates continuous synthetic gaze and gesture trajectories across test targets."""
        step = 0
        t0 = time.time()

        # Center approximations for 1920x1080 layout
        # (Cards arranged in responsive grid: row 1 targets at y~240, row 2 at y~540)
        target_coords = [
            (320, 240, "PRIMARY_CLICK", "PINCH_INDEX", "TB-T01"),
            (680, 240, "HOVER", "NONE", "TB-T02"),
            (1040, 240, "SECONDARY_CLICK", "PINCH_MIDDLE", "TB-T03"),
            (1400, 240, "PRIMARY_CLICK", "PINCH_INDEX", "TB-T04"),
            (320, 540, "PRIMARY_CLICK", "PINCH_INDEX", "TB-T05"),
            (680, 540, "SCROLL_DOWN", "SWIPE_DOWN", "TB-T06"),
            (1040, 540, "CONFIRM_SUBMIT", "NONE", "TB-T07"),
            (1400, 540, "NO_ACTION", "NONE", "TB-T08"),
        ]

        while self._running:
            now = time.time()
            dt = now - t0

            # Cycle through targets every 3.5 seconds
            cycle_idx = int(dt / 3.5) % len(target_coords)
            target_x, target_y, target_cmd, target_token, _ = target_coords[cycle_idx]

            # Natural saccadic micro-jitter
            jitter_x = math.sin(dt * 8.0) * 10.0
            jitter_y = math.cos(dt * 7.0) * 8.0
            gx = target_x + jitter_x
            gy = target_y + jitter_y

            # Trigger gesture halfway into the target fixation
            sub_time = dt % 3.5
            if 1.5 <= sub_time <= 1.8:
                token = target_token
                cmd = target_cmd
                conf = 0.95
            else:
                token = "NONE"
                cmd = "NO_ACTION"
                conf = 0.0

            if self.server is not None:
                norm_gx = float(np.clip(gx / 1920.0, 0.0, 1.0))
                norm_gy = float(np.clip(gy / 1080.0, 0.0, 1.0))
                self.server.broadcast_perception(
                    gaze_x=gx,
                    gaze_y=gy,
                    active_mode="GESTURE",
                    gesture_token=token,
                    gesture_confidence=conf,
                    command=cmd,
                    timestamp=now,
                    gaze_fixated=True,
                    norm_gaze_x=norm_gx,
                    norm_gaze_y=norm_gy,
                )

            step += 1
            time.sleep(1.0 / 60.0)

    def _run_live_loop(self) -> None:
        """Executes live camera-based multimodal perception pipeline."""
        if self.stream is None:
            return

        scr_w, scr_h = get_screen_dimensions()
        pipeline = FeaturePipeline(camera_fov_degrees=60.0, screen_width=scr_w, screen_height=scr_h)
        classifier = GestureClassifier()
        arbiter = ModalityArbiter(enable_pynput_hooks=False)
        composer = CommandComposer()
        profile = self.coordinator.current_profile
        logger.info(f"Loaded user profile '{self.user_id}' (version {profile.version_id}) on {scr_w}x{scr_h} display")

        while self._running:
            try:
                raw_frame = self.stream.read_latest_frame(wait_timeout_sec=0.05)
                if raw_frame is None or raw_frame.image is None:
                    time.sleep(0.005)
                    continue

                active_prof = self.coordinator.current_profile

                # 1. Perception
                perc_frame = pipeline.process_frame(raw_frame, profile=active_prof)

                # 2. Gesture Classification
                gesture_out = classifier.classify(perc_frame.hand, timestamp_ms=perc_frame.timestamp_ms)

                # 3. Modality Arbiter
                arb_gesture, active_mode = arbiter.arbitrate(gesture_out, timestamp_ms=perc_frame.timestamp_ms)

                # 4. Command Composition
                composed_cmd = composer.compose(perc_frame, arb_gesture, profile=active_prof)

                # 5. Broadcast to Testbench Frontend
                if self.server is not None:
                    gx, gy = perc_frame.gaze_screen_xy
                    is_fixated = (perc_frame.gaze_dwell_ms > 100.0) or (perc_frame.gaze_stability > 0.8)
                    token_str = (
                        arb_gesture.gesture_token.value
                        if hasattr(arb_gesture.gesture_token, "value")
                        else str(arb_gesture.gesture_token)
                    )
                    norm_gx = float(np.clip(gx / float(scr_w), 0.0, 1.0))
                    norm_gy = float(np.clip(gy / float(scr_h), 0.0, 1.0))
                    self.server.broadcast_perception(
                        gaze_x=float(gx),
                        gaze_y=float(gy),
                        active_mode=active_mode.value,
                        gesture_token=token_str,
                        gesture_confidence=float(arb_gesture.c_gesture),
                        command=composed_cmd.action_type.value,
                        timestamp=time.time(),
                        gaze_fixated=is_fixated,
                        norm_gaze_x=norm_gx,
                        norm_gaze_y=norm_gy,
                    )

            except Exception as loop_err:
                logger.error("Error in live perception loop: %s", loop_err)
                time.sleep(0.02)

    def stop(self) -> None:
        """Stops the testbench server and hardware streams."""
        self._running = False
        if self.stream is not None:
            self.stream.stop()
            self.stream = None
        if self.server is not None:
            self.server.stop()
            self.server = None

        # Persist the final profile snapshot to data/profiles/{user_id}.json on disk
        if self._interaction_count > 0:
            saved = self.profile_mgr.save_profile(self.coordinator.current_profile)
            if saved:
                print(f"[ONLINE LEARNING] Profile '{self.user_id}' (version {self.coordinator.current_profile.version_id}) permanently saved to data/profiles/{self.user_id}.json")

        print(f"\n[SESSION COMPLETE] Recorded {self._interaction_count} verified UI target interactions.")


def main() -> None:
    """Entry point for the interactive testbench runner."""
    parser = argparse.ArgumentParser(description="Multimodal HCI Test Bench Suite Launcher")
    parser.add_argument("--camera", type=int, default=0, help="Camera device ID (default: 0)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="HTTP/WebSocket port (default: 8080)")
    parser.add_argument("--simulated", action="store_true", help="Run with simulated synthetic perception trajectory")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open web browser")
    parser.add_argument("--user", type=str, default="default_user", help="User profile ID to load (default: default_user)")

    args = parser.parse_args()

    runner = TestbenchRunner(
        camera_id=args.camera,
        host=args.host,
        port=args.port,
        simulated=args.simulated,
        launch_browser=not args.no_browser,
        user_id=args.user,
    )

    def sig_handler(sig, frame):
        print("\nTermination signal received. Shutting down Test Bench Suite...")
        runner.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    try:
        runner.run()
    except KeyboardInterrupt:
        runner.stop()


if __name__ == "__main__":
    main()
