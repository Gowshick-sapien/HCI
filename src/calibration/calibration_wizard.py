"""
Interactive Multi-Pass Desktop Gaze Calibration Wizard GUI.
Fullscreen PySide6 application that guides the user through a relaxed, multi-pass spatial gaze acquisition,
fits coupled eye-head mapping matrices, estimates neutral head orientation,
and persists the personalized ProfileSnapshot.

Usage:
    python src/calibration/calibration_wizard.py
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import numpy as np
from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
)

from src.calibration.gaze_calibrator import (
    CalibrationPointSample,
    GazeCalibrationResult,
    GazeCalibrator,
)
from src.calibration.head_pose_calibrator import (
    HeadPoseCalibrationResult,
    HeadPoseCalibrator,
)
from src.capture.frame_types import CameraConfig
from src.capture.video_stream import VideoStream
from src.perception.feature_pipeline import FeaturePipeline
from src.storage.profile_manager import ProfileManager
from src.storage.schemas import ProfileSnapshot

logger = logging.getLogger(__name__)


class VideoPerceptionWorker(QThread):
    """Asynchronous background worker that processes camera frames during calibration."""
    sample_ready = Signal(object)

    def __init__(self, camera_id: int = 0) -> None:
        super().__init__()
        self.camera_id = camera_id
        self._running = False
        self.stream: Optional[VideoStream] = None
        self.pipeline: Optional[FeaturePipeline] = None

    def run(self) -> None:
        self._running = True
        config = CameraConfig(camera_id=self.camera_id, frame_width=640, frame_height=480, target_fps=30)
        self.stream = VideoStream(config)
        if not self.stream.start():
            print("ERROR: Could not open camera for calibration.")
            return

        self.pipeline = FeaturePipeline()

        while self._running:
            raw_frame = self.stream.read_latest_frame(wait_timeout_sec=0.05)
            if raw_frame and raw_frame.image is not None:
                perc_frame = self.pipeline.process_frame(raw_frame)
                self.sample_ready.emit(perc_frame)
            else:
                self.msleep(10)

        if self.stream:
            self.stream.stop()
        if self.pipeline:
            self.pipeline.close()

    def stop(self) -> None:
        self._running = False
        self.wait(1000)


class CalibrationWizardWidget(QWidget):
    """Interactive fullscreen canvas displaying relaxed, multi-pass calibration target points."""
    calibration_finished = Signal(object, object)

    def __init__(self, user_id: str = "default_user", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.user_id = user_id

        # 14-Target Multi-Pass Sequence:
        # Pass 1: Center -> 8 perimeter points (primary calibration)
        # Pass 2: Center -> 4 corners (verification & refinement)
        self.target_schedule = [
            # --- PASS 1 ---
            (0.50, 0.50, "Center (Neutral Anchor)"),
            (0.10, 0.10, "Top-Left"),
            (0.50, 0.10, "Top-Center"),
            (0.90, 0.10, "Top-Right"),
            (0.10, 0.50, "Mid-Left"),
            (0.90, 0.50, "Mid-Right"),
            (0.10, 0.90, "Bottom-Left"),
            (0.50, 0.90, "Bottom-Center"),
            (0.90, 0.90, "Bottom-Right"),
            # --- PASS 2 (Refinement) ---
            (0.50, 0.50, "Center Verification"),
            (0.10, 0.10, "Top-Left Refinement"),
            (0.90, 0.10, "Top-Right Refinement"),
            (0.10, 0.90, "Bottom-Left Refinement"),
            (0.90, 0.90, "Bottom-Right Refinement"),
        ]

        self.current_step = 0
        self.recorded_samples: List[CalibrationPointSample] = []
        self.neutral_head_samples: List[Tuple[float, float, float]] = []

        # Smooth ergonomic pacing configuration
        # Settle: ~1.0s (30 frames) for relaxed visual reaction & head positioning
        # Hold: ~2.0s (60 frames) for stable fixation accumulation
        self.point_phase = "SETTLE" # "SETTLE" | "HOLD"
        self.settle_frame_count = 0
        self.SETTLE_FRAMES_REQUIRED = 28 # ~0.95 seconds settle window
        self.HOLD_FRAMES_REQUIRED = 55   # ~1.85 seconds steady acquisition

        self._current_point_rx: List[float] = []
        self._current_point_ry: List[float] = []
        self._current_point_yaw: List[float] = []
        self._current_point_pitch: List[float] = []

        # Animated gliding target coordinates
        self.anim_target_x = 0.50
        self.anim_target_y = 0.50

        self.state = "WELCOME" # "WELCOME" | "CALIBRATING" | "SUMMARY"
        self.status_message = "Press SPACE to Begin Multi-Pass Calibration"
        self.last_gaze_result: Optional[GazeCalibrationResult] = None
        self.last_head_result: Optional[HeadPoseCalibrationResult] = None

        # 60 FPS animation timer
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._on_anim_tick)
        self.anim_timer.start(16)

    def _on_anim_tick(self) -> None:
        """Smoothly interpolates target position during transitions."""
        if self.state == "CALIBRATING" and self.current_step < len(self.target_schedule):
            dest_x, dest_y, _ = self.target_schedule[self.current_step]
            # Exponential ease towards destination
            self.anim_target_x += (dest_x - self.anim_target_x) * 0.12
            self.anim_target_y += (dest_y - self.anim_target_y) * 0.12
        self.update()

    def start_calibration(self) -> None:
        self.current_step = 0
        self.anim_target_x, self.anim_target_y, _ = self.target_schedule[0]
        self.point_phase = "SETTLE"
        self.settle_frame_count = 0
        self.recorded_samples.clear()
        self.neutral_head_samples.clear()
        self._clear_current_point_buffers()
        self.state = "CALIBRATING"
        self.status_message = "Follow the dot and relax your posture..."

    def _clear_current_point_buffers(self) -> None:
        self.point_phase = "SETTLE"
        self.settle_frame_count = 0
        self._current_point_rx.clear()
        self._current_point_ry.clear()
        self._current_point_yaw.clear()
        self._current_point_pitch.clear()

    def process_perception_frame(self, perc_frame) -> None:
        """Processes live camera frames with relaxed pacing and robust IQR trimming."""
        if self.state != "CALIBRATING":
            return

        if perc_frame.eye.confidence > 0.0:
            rx = perc_frame.eye.iris_ratio_x
            ry = perc_frame.eye.iris_ratio_y
            yaw, pitch, roll = perc_frame.head_euler_angles

            # 1. Saccadic Settle Phase: Discard initial transit frames
            if self.point_phase == "SETTLE":
                self.settle_frame_count += 1
                if self.settle_frame_count >= self.SETTLE_FRAMES_REQUIRED:
                    self.point_phase = "HOLD"
                return

            # 2. Fixation Hold Phase: Record steady frames
            self._current_point_rx.append(rx)
            self._current_point_ry.append(ry)
            self._current_point_yaw.append(yaw)
            self._current_point_pitch.append(pitch)
            self.neutral_head_samples.append((yaw, pitch, roll))

            if len(self._current_point_rx) >= self.HOLD_FRAMES_REQUIRED:
                self._finish_current_step()

    def _finish_current_step(self) -> None:
        w, h = self.width(), self.height()
        tx_norm, ty_norm, label = self.target_schedule[self.current_step]
        target_xy = (tx_norm * w, ty_norm * h)

        # Robust IQR Trimmed Mean (discards top/bottom 15% noise outliers)
        def trimmed_mean(arr_list: List[float], trim_pct: float = 0.15) -> float:
            arr = np.sort(np.array(arr_list))
            n = len(arr)
            k = int(n * trim_pct)
            trimmed = arr[k:n - k] if n - 2 * k > 0 else arr
            return float(np.median(trimmed))

        sample = CalibrationPointSample(
            target_screen_xy=target_xy,
            iris_ratio_x_mean=trimmed_mean(self._current_point_rx),
            iris_ratio_y_mean=trimmed_mean(self._current_point_ry),
            head_yaw_mean=trimmed_mean(self._current_point_yaw),
            head_pitch_mean=trimmed_mean(self._current_point_pitch),
            sample_count=len(self._current_point_rx)
        )
        self.recorded_samples.append(sample)

        self.current_step += 1
        self._clear_current_point_buffers()

        if self.current_step >= len(self.target_schedule):
            self._finalize_calibration()

    def _finalize_calibration(self) -> None:
        self.state = "SUMMARY"
        self.status_message = "Computing Coupled Eye-Head Calibration..."

        try:
            gaze_calibrator = GazeCalibrator(screen_width=self.width(), screen_height=self.height())
            head_calibrator = HeadPoseCalibrator()

            gaze_result = gaze_calibrator.solve(self.recorded_samples)
            head_result = head_calibrator.fit(self.neutral_head_samples)

            self.last_gaze_result = gaze_result
            self.last_head_result = head_result

            self.calibration_finished.emit(gaze_result, head_result)
        except Exception as e:
            print(f"ERROR finalizing calibration: {e}")
            self.state = "WELCOME"

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Background
        painter.fillRect(0, 0, w, h, QColor(18, 18, 18))

        if self.state == "WELCOME":
            # Welcome Screen
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
            painter.drawText(QRectF(0, h * 0.30, w, 60), Qt.AlignmentFlag.AlignCenter, "Personalized Desktop Gaze Calibration")

            painter.setFont(QFont("Segoe UI", 14))
            painter.setPen(QColor(200, 200, 200))
            painter.drawText(QRectF(0, h * 0.40, w, 35), Qt.AlignmentFlag.AlignCenter, "Paced Multi-Pass Calibration (Pass 1: 9 Points | Pass 2: 5 Checkpoints)")
            painter.drawText(QRectF(0, h * 0.46, w, 35), Qt.AlignmentFlag.AlignCenter, "1. Follow the gliding dot as it moves smoothly across your screen.")
            painter.drawText(QRectF(0, h * 0.51, w, 35), Qt.AlignmentFlag.AlignCenter, "2. When it settles, look naturally at the center until the circle completes.")
            painter.drawText(QRectF(0, h * 0.56, w, 35), Qt.AlignmentFlag.AlignCenter, "Both eyes and head posture are recorded together with relaxed timing.")

            painter.setFont(QFont("Segoe UI", 16, QFont.Weight.DemiBold))
            painter.setPen(QColor(0, 255, 200))
            painter.drawText(QRectF(0, h * 0.68, w, 40), Qt.AlignmentFlag.AlignCenter, "[ Press SPACE to Begin | ESC to Exit ]")
            return

        elif self.state == "SUMMARY":
            # Summary Card
            card_w, card_h = 680, 440
            card_x = (w - card_w) / 2.0
            card_y = (h - card_h) / 2.0

            painter.setBrush(QBrush(QColor(28, 28, 28)))
            painter.setPen(QPen(QColor(0, 255, 200), 2))
            painter.drawRoundedRect(QRectF(card_x, card_y, card_w, card_h), 16, 16)

            # Title
            painter.setPen(QColor(0, 255, 200))
            painter.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
            painter.drawText(QRectF(card_x, card_y + 25, card_w, 40), Qt.AlignmentFlag.AlignCenter, "Personalized Calibration Complete")

            if self.last_gaze_result:
                grade_color = QColor(0, 255, 120) if self.last_gaze_result.is_valid else QColor(255, 140, 0)
                painter.setPen(grade_color)
                painter.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))
                painter.drawText(QRectF(card_x, card_y + 85, card_w, 35), Qt.AlignmentFlag.AlignCenter, f"Quality Grade: {self.last_gaze_result.calibration_grade}")

                painter.setPen(QColor(220, 220, 220))
                painter.setFont(QFont("Segoe UI", 13))
                painter.drawText(QRectF(card_x, card_y + 135, card_w, 28), Qt.AlignmentFlag.AlignCenter, f"Coupled Residual RMSE: {self.last_gaze_result.rmse_pixels:.1f} px")
                painter.drawText(QRectF(card_x, card_y + 168, card_w, 28), Qt.AlignmentFlag.AlignCenter, f"Mean Absolute Coordinate Error: {self.last_gaze_result.mae_pixels:.1f} px")
                painter.drawText(QRectF(card_x, card_y + 201, card_w, 28), Qt.AlignmentFlag.AlignCenter, f"Max Coordinate Error: {self.last_gaze_result.max_error_pixels:.1f} px")
                painter.drawText(QRectF(card_x, card_y + 234, card_w, 28), Qt.AlignmentFlag.AlignCenter, f"Total Acquisition Points: {len(self.recorded_samples)} (Multi-Pass Verified)")

                painter.setPen(QColor(160, 200, 255))
                painter.drawText(QRectF(card_x, card_y + 280, card_w, 28), Qt.AlignmentFlag.AlignCenter, f"Profile Saved: data/profiles/{self.user_id}.json")

            painter.setPen(QColor(0, 255, 200))
            painter.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
            painter.drawText(QRectF(card_x, card_y + 355, card_w, 40), Qt.AlignmentFlag.AlignCenter, "[ Press SPACE or ENTER to Save & Exit | 'r' to Re-Calibrate ]")
            return

        # Target Rendering during CALIBRATING with smooth gliding
        dest_tx, dest_ty, label = self.target_schedule[min(self.current_step, len(self.target_schedule) - 1)]
        px = self.anim_target_x * w
        py = self.anim_target_y * h

        pass_num = 1 if self.current_step < 9 else 2
        total_steps = len(self.target_schedule)

        # Outer ring
        painter.setBrush(Qt.BrushStyle.NoBrush)
        if self.point_phase == "SETTLE":
            # Yellow pulsing ring during settle phase (~1.0s)
            settle_progress = self.settle_frame_count / float(self.SETTLE_FRAMES_REQUIRED)
            pulse_rad = int(32 - 6 * settle_progress)
            painter.setPen(QPen(QColor(255, 215, 0), 2, Qt.PenStyle.DashLine))
            painter.drawEllipse(QPointF(px, py), pulse_rad, pulse_rad)
            painter.setPen(QColor(255, 215, 0))
            painter.setFont(QFont("Segoe UI", 12))
            painter.drawText(QRectF(px - 120, py + 42, 240, 25), Qt.AlignmentFlag.AlignCenter, "Looking at target...")
        else:
            # Cyan ring with smooth progress arc during hold phase (~2.0s)
            progress = min(1.0, len(self._current_point_rx) / float(self.HOLD_FRAMES_REQUIRED))
            painter.setPen(QPen(QColor(80, 80, 80), 3))
            painter.drawEllipse(QPointF(px, py), 28, 28)

            painter.setPen(QPen(QColor(0, 255, 200), 5))
            span_angle = int(progress * 360 * 16)
            painter.drawArc(QRectF(px - 28, py - 28, 56, 56), 90 * 16, -span_angle)

            painter.setPen(QColor(0, 255, 200))
            painter.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
            painter.drawText(QRectF(px - 120, py + 42, 240, 25), Qt.AlignmentFlag.AlignCenter, "Hold steady...")

        # Center dot
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(px, py), 9, 9)

        # Bottom status bar
        painter.setFont(QFont("Segoe UI", 13))
        painter.setPen(QColor(200, 200, 200))
        status = f"Step {self.current_step + 1} of {total_steps} [Pass {pass_num}] - {label}"
        painter.drawText(QRectF(0, h - 55, w, 35), Qt.AlignmentFlag.AlignCenter, status)


class CalibrationWizardWindow(QMainWindow):
    """Main application window managing the wizard lifecycle and profile persistence."""

    def __init__(self, user_id: str = "default_user") -> None:
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("Adaptive Multimodal HCI - Calibration Wizard")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

        self.widget = CalibrationWizardWidget(user_id=self.user_id, parent=self)
        self.setCentralWidget(self.widget)

        self.worker = VideoPerceptionWorker(camera_id=0)
        self.worker.sample_ready.connect(self.widget.process_perception_frame)
        self.widget.calibration_finished.connect(self.on_calibration_finished)

        self.worker.start()
        self.showFullScreen()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Space:
            if self.widget.state == "WELCOME":
                self.widget.start_calibration()
            elif self.widget.state == "SUMMARY":
                self.close()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.widget.state == "SUMMARY":
                self.close()
        elif event.key() == Qt.Key.Key_R:
            if self.widget.state == "SUMMARY":
                self.widget.start_calibration()
        elif event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Q):
            self.close()

    def on_calibration_finished(self, gaze_res: GazeCalibrationResult, head_res: HeadPoseCalibrationResult) -> None:
        try:
            profile_mgr = ProfileManager()
            existing_profile = profile_mgr.load_profile(self.user_id)

            existing_profile.gaze_calibration_matrix = [list(row) for row in gaze_res.affine_matrix_3x3]
            existing_profile.neutral_pose_mean = list(head_res.mean_euler_angles)
            existing_profile.neutral_pose_cov_inv = [list(row) for row in head_res.precision_matrix_3x3]
            existing_profile.last_recalibration_timestamp = time.time()
            existing_profile.recalibration_count += 1

            profile_mgr.save_profile(existing_profile)
            print(f"\n[CALIBRATION SUCCESS] Saved profile for '{self.user_id}' with RMSE: {gaze_res.rmse_pixels:.2f} px")
        except Exception as e:
            print(f"ERROR saving profile: {e}")

    def closeEvent(self, event) -> None:
        self.worker.stop()
        event.accept()


def main():
    app = QApplication(sys.argv)
    user_id = sys.argv[1] if len(sys.argv) > 1 else "default_user"
    window = CalibrationWizardWindow(user_id=user_id)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
