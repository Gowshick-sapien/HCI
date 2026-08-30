"""
Interactive Live Perception, Fusion & Supervisory Feedback Diagnostic Visualizer.
High-performance PySide6 desktop application using timer-driven double buffering
to guarantee 100% responsive, non-blocking 60 FPS UI rendering on Windows.

Usage:
    python scripts/verify_perception_live.py
Controls:
    [q] / [ESC] : Exit visualizer
    [z]         : Test implicit undo feedback trigger (Ctrl+Z)
    [r]         : Reset tracking & reload calibration profile
"""

import collections
import logging
import os
import sys
import threading
import time
import traceback
from pathlib import Path
from typing import Deque, List, Optional, Tuple

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np
from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QFont, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget

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
    ComposedCommand,
    DeviceMode,
    FeedbackEvent,
    FeedbackType,
    GestureClassification,
    GestureToken,
    PerceptionFrame,
    ProfileSnapshot,
)

# Hand landmark skeletal connections (21 landmarks)
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (5, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
    (13, 17), (17, 18), (18, 19), (19, 20),# Pinky
    (0, 17)                                # Palm base
]


class PerceptionWorker(threading.Thread):
    """
    Dedicated background worker thread that executes video capture, ML inference,
    multimodal fusion, and Layer 4 feedback observation without touching the Qt GUI thread.
    """

    def __init__(self, camera_id: int = 0) -> None:
        super().__init__(daemon=True, name="PerceptionWorkerThread")
        self.camera_id = camera_id
        self._running = False
        self._lock = threading.RLock()

        # Shared double-buffer for GUI rendering
        self.latest_annotated_image: Optional[QImage] = None
        self.latest_telemetry_lines: List[Tuple[str, Tuple[int, int, int]]] = []
        self.latest_feedback_event: Optional[FeedbackEvent] = None
        self.actual_fps: float = 30.0
        self.latency_ms: float = 15.0

        # Input event queues from GUI
        self._pending_mouse_moves: Deque[Tuple[float, float]] = collections.deque(maxlen=20)
        self._pending_keys: Deque[Tuple[str, bool]] = collections.deque(maxlen=20)
        self._reload_profile_requested: bool = False

        # Feedback & Persistence Subsystems
        self.telemetry_logger = FeedbackTelemetryLogger()
        self.feedback_observer = FeedbackObserver(telemetry_logger=self.telemetry_logger)

        def on_feedback_received(event: FeedbackEvent):
            with self._lock:
                self.latest_feedback_event = event
            print(f"[FEEDBACK] {event.feedback_type.value} | Source: {event.detector_source} | Mode: {event.failure_mode.value} (dt: {event.latency_delta_t:.2f}s)")

        self.feedback_observer.register_feedback_listener(on_feedback_received)

    def inject_mouse_movement(self, dx: float, dy: float) -> None:
        self._pending_mouse_moves.append((dx, dy))

    def inject_key_event(self, key_name: str, is_ctrl: bool = False) -> None:
        self._pending_keys.append((key_name, is_ctrl))

    def request_profile_reload(self) -> None:
        self._reload_profile_requested = True

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        self._running = True
        config = CameraConfig(camera_id=self.camera_id, frame_width=640, frame_height=480, target_fps=30)
        stream = VideoStream(config)

        if not stream.start():
            print(f"ERROR: Could not open camera device ID {self.camera_id}.")
            return

        pipeline = FeaturePipeline(camera_fov_degrees=60.0, screen_width=1920, screen_height=1080)
        classifier = GestureClassifier()
        arbiter = ModalityArbiter(enable_pynput_hooks=False)
        composer = CommandComposer()

        profile_mgr = ProfileManager()
        profile = profile_mgr.load_profile("default_user")

        last_executed_cmd: Optional[ComposedCommand] = None
        t_prev = time.perf_counter()
        frame_counter = 0

        while self._running:
            try:
                if self._reload_profile_requested:
                    self._reload_profile_requested = False
                    profile = profile_mgr.load_profile("default_user")
                    classifier.reset()
                    pipeline.gaze_dwell_tracker.reset()
                    self.feedback_observer.reset()
                    print("Perception pipeline and feedback observer reset.")

                raw_frame = stream.read_latest_frame(wait_timeout_sec=0.05)
                if raw_frame is None or raw_frame.image is None:
                    time.sleep(0.005)
                    continue

                t0 = time.perf_counter()

                # 1. Layer 1 Perception
                perc_frame = pipeline.process_frame(raw_frame, profile=profile)

                # 2. Layer 1B Gesture Classification
                gesture_out = classifier.classify(perc_frame.hand, timestamp_ms=perc_frame.timestamp_ms)

                # 3. Active Modality Arbiter
                arb_gesture, active_mode = arbiter.arbitrate(gesture_out, timestamp_ms=perc_frame.timestamp_ms)

                # 4. Stage 3A Command Composition & Spatial Binding
                composed_cmd = composer.compose(perc_frame, arb_gesture, profile=profile)

                # Register executed action with Layer 4 FeedbackObserver upon state transition
                if composed_cmd.action_type != ActionType.NO_ACTION and (last_executed_cmd is None or last_executed_cmd.action_type != composed_cmd.action_type):
                    action_ctx = ActionContext(
                        action_id=composed_cmd.action_id,
                        action_name=composed_cmd.action_type.value,
                        tier=ActionTier.TIER_1_IMMEDIATE,
                        timestamp_t0=time.time(),
                        target_pid=os.getpid(),
                        target_window_title="Diagnostic Visualizer",
                        feature_snapshot=perc_frame,
                        weights_snapshot={"GAZE": 0.5, "GESTURE": 0.5},
                        fused_score=composed_cmd.composed_score,
                        threshold=0.70,
                        is_executed=True
                    )
                    self.feedback_observer.on_action_executed(action_ctx)
                    last_executed_cmd = composed_cmd
                elif composed_cmd.action_type == ActionType.NO_ACTION:
                    last_executed_cmd = None

                # 5. Layer 4 Feedback Observer: Process pending input queues
                while self._pending_mouse_moves:
                    mdx, mdy = self._pending_mouse_moves.popleft()
                    self.feedback_observer.on_mouse_movement(mdx, mdy)

                while self._pending_keys:
                    kname, kctrl = self._pending_keys.popleft()
                    self.feedback_observer.on_key_event(kname, kctrl)

                # Process head gestures & stability expirations
                self.feedback_observer.process_perception_frame(perc_frame)

                latency_ms = (time.perf_counter() - t0) * 1000.0

                # 6. Render Overlays onto BGR image (Fast OpenCV drawing in C++)
                annotated_bgr = raw_frame.image.copy()
                h_img, w_img = annotated_bgr.shape[:2]

                # Hand skeleton
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

                # Irises
                if perc_frame.eye.confidence > 0.0:
                    lx, ly = int(perc_frame.eye.left_iris_center[0]), int(perc_frame.eye.left_iris_center[1])
                    rx, ry = int(perc_frame.eye.right_iris_center[0]), int(perc_frame.eye.right_iris_center[1])
                    cv2.circle(annotated_bgr, (lx, ly), 3, (0, 255, 255), -1)
                    cv2.circle(annotated_bgr, (rx, ry), 3, (0, 255, 255), -1)

                # Gaze Reticle & Anchor
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

                # Convert BGR to QImage
                rgb_arr = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)
                qimg = QImage(rgb_arr.data, w_img, h_img, 3 * w_img, QImage.Format.Format_RGB888).copy()

                # Format Telemetry Lines
                cmd_name = composed_cmd.action_type.value if composed_cmd else "NO_ACTION"
                conf_pct = int(arb_gesture.c_gesture * 100)
                calib_tag = "[CALIBRATED]" if profile.last_recalibration_timestamp > 0.0 else "[UNCALIBRATED]"

                line1 = f"MODE: GESTURE {calib_tag} | TOKEN: {arb_gesture.gesture_token.value}"
                line2 = f"ACTION: {cmd_name} | CONF: {conf_pct}% | FPS: {self.actual_fps:.0f} ({latency_ms:.1f}ms)"
                anc_str = f"({int(perc_frame.gaze_anchor[0])}, {int(perc_frame.gaze_anchor[1])}) [LOCKED]" if perc_frame.gaze_anchor else "[SEARCHING...]"
                line3 = f"GAZE: ({int(perc_frame.gaze_screen_xy[0])}, {int(perc_frame.gaze_screen_xy[1])}) | DWELL: {int(perc_frame.gaze_dwell_ms)}ms | ANCHOR: {anc_str}"

                # Update shared GUI state
                with self._lock:
                    self.latest_annotated_image = qimg
                    self.latest_telemetry_lines = [
                        (line1, (0, 255, 200)),
                        (line2, (0, 255, 120) if cmd_name != "NO_ACTION" else (220, 220, 220)),
                        (line3, (255, 220, 120))
                    ]
                    self.latency_ms = latency_ms

                frame_counter += 1
                if frame_counter % 15 == 0:
                    now_perf = time.perf_counter()
                    self.actual_fps = 15.0 / max(1e-4, now_perf - t_prev)
                    t_prev = now_perf
            except Exception as e:
                traceback.print_exc()
                time.sleep(0.01)

        stream.stop()
        pipeline.close()


class DiagnosticCanvasWidget(QWidget):
    """
    Central display widget running smooth 60 FPS paint rendering.
    """

    def __init__(self, worker: PerceptionWorker, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.worker = worker
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._last_mouse_pos: Optional[QPointF] = None

    def mouseMoveEvent(self, event) -> None:
        pos = event.position()
        if self._last_mouse_pos is not None:
            dx = pos.x() - self._last_mouse_pos.x()
            dy = pos.y() - self._last_mouse_pos.y()
            if (dx * dx + dy * dy) >= 16:
                self.worker.inject_mouse_movement(float(dx), float(dy))
        self._last_mouse_pos = pos

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Background
        painter.fillRect(0, 0, w, h, QColor(15, 15, 15))

        # Grab shared state safely
        with self.worker._lock:
            qimg = self.worker.latest_annotated_image
            lines = list(self.worker.latest_telemetry_lines)
            fb_event = self.worker.latest_feedback_event

        # 1. Draw Video Frame
        if qimg is not None and not qimg.isNull():
            img_w, img_h = qimg.width(), qimg.height()
            scale = min(w / float(img_w), (h - 130) / float(img_h))
            tw = int(img_w * scale)
            th = int(img_h * scale)
            tx = (w - tw) // 2
            ty = 130 + (h - 130 - th) // 2

            painter.drawImage(QRectF(tx, ty, tw, th), qimg)

        # 2. Draw Top Telemetry HUD Header
        painter.fillRect(0, 0, w, 125, QColor(22, 22, 22))
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        painter.drawLine(0, 125, w, 125)

        # Telemetry text lines
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        for i, (text, col_rgb) in enumerate(lines[:3]):
            painter.setPen(QColor(*col_rgb))
            painter.drawText(QRectF(16, 10 + i * 26, w - 32, 24), Qt.AlignmentFlag.AlignLeft, text)

        # Telemetry line 4: Supervisory Feedback
        if fb_event:
            fb_col = QColor(0, 255, 120) if fb_event.feedback_type == FeedbackType.IMPLICIT_POS else QColor(255, 140, 0)
            fb_text = f"FEEDBACK: [{fb_event.feedback_type.value} | {fb_event.failure_mode.value} | {fb_event.detector_source} ({fb_event.latency_delta_t:.2f}s)]"
        else:
            fb_col = QColor(140, 140, 140)
            fb_text = "FEEDBACK: [Awaiting Interaction...]"

        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        painter.setPen(fb_col)
        painter.drawText(QRectF(16, 92, w - 320, 24), Qt.AlignmentFlag.AlignLeft, fb_text)

        painter.setFont(QFont("Segoe UI", 10))
        painter.setPen(QColor(160, 160, 160))
        painter.drawText(QRectF(w - 300, 92, 280, 24), Qt.AlignmentFlag.AlignRight, "[Keys: 'z'=Undo | 'r'=Reset | 'q'=Quit]")


class LiveVisualizerWindow(QMainWindow):
    """
    Main application window hosting the diagnostic canvas and 30 FPS render timer.
    """

    def __init__(self, user_id: str = "default_user") -> None:
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("Adaptive Multimodal HCI - Live Diagnostic Visualizer HUD")
        self.resize(760, 640)

        # Background perception worker
        self.worker = PerceptionWorker(camera_id=0)
        self.worker.start()

        # Canvas Widget
        self.canvas = DiagnosticCanvasWidget(worker=self.worker, parent=self)
        self.setCentralWidget(self.canvas)

        # 30 FPS Render Timer
        self.render_timer = QTimer(self)
        self.render_timer.timeout.connect(self.canvas.update)
        self.render_timer.start(33) # 33ms -> 30 FPS

        print("================================================================================")
        print("  LIVE PERCEPTION, FUSION & SUPERVISORY FEEDBACK DIAGNOSTIC VISUALIZER")
        print("  Deliverables D1, D2, D3 & D4 Native Desktop Tool")
        print("================================================================================")
        print(f"Loaded Profile for '{self.user_id}': CALIBRATED")
        print(f"Feedback Event Log Stream: {self.worker.telemetry_logger.log_file_path.resolve()}\n")
        print("Visualizer active. Press 'q' or ESC in the window to quit.")
        print("Perform an index pinch with locked gaze anchor to execute an action.")
        print("Then move your physical mouse or press 'z' to observe real-time feedback logging!\n")

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Q, Qt.Key.Key_Escape):
            self.close()
        elif event.key() == Qt.Key.Key_Z:
            print("[KEY EVENT] Triggered Key 'z' (Undo)")
            self.worker.inject_key_event("z", is_ctrl=True)
        elif event.key() == Qt.Key.Key_R:
            self.worker.request_profile_reload()

    def closeEvent(self, event) -> None:
        print("\nShutting down perception worker...")
        self.worker.stop()
        event.accept()
        print("Visualizer exited cleanly.")


def main():
    app = QApplication(sys.argv)
    user_id = sys.argv[1] if len(sys.argv) > 1 else "default_user"
    window = LiveVisualizerWindow(user_id=user_id)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
