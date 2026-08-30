"""
Deliverable E2: State-Aware Explainability HUD Overlay Window.
Semi-transparent, borderless, click-through desktop overlay for real-time multimodal feedback.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QApplication, QWidget

from src.storage.schemas import (
    ActionType,
    AssessmentMetrics,
    ComposedCommand,
    DeviceMode,
    FeedbackEvent,
    MacroPolicy,
    PerceptionFrame,
    SystemHealthState,
)

logger = logging.getLogger(__name__)


class ExplainabilityHUDOverlay(QWidget):
    """
    Semi-transparent, click-through desktop HUD window.
    Renders live confidence breakdowns, Tier-2 dwell confirmation rings,
    active health state badges, and device modality indicators.
    """

    def __init__(
        self,
        screen_width: int = 1920,
        screen_height: int = 1080,
        target_fps: int = 60,
        parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.screen_width = int(screen_width)
        self.screen_height = int(screen_height)
        self.target_fps = int(target_fps)

        self._lock = threading.RLock()

        # Telemetry & pipeline state buffers
        self._current_perception: Optional[PerceptionFrame] = None
        self._current_command: Optional[ComposedCommand] = None
        self._current_metrics: Optional[AssessmentMetrics] = None
        self._current_feedback: Optional[FeedbackEvent] = None
        self._active_device_mode: DeviceMode = DeviceMode.GESTURE
        self._active_weights: Dict[str, float] = {"EYE": 0.40, "HEAD": 0.30, "HAND": 0.30}
        self._last_paint_duration_ms: float = 0.0

        # Configure click-through translucent window attributes
        self._setup_window_flags()

        # Setup 60 FPS Render Timer
        self._render_timer = QTimer(self)
        self._render_timer.timeout.connect(self.update)
        frame_interval_ms = max(16, int(1000.0 / self.target_fps))
        self._render_timer.start(frame_interval_ms)

    def _setup_window_flags(self) -> None:
        """Configures native OS click-through transparency flags."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowTransparentForInput |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setGeometry(0, 0, self.screen_width, self.screen_height)

    def update_telemetry(
        self,
        perception: Optional[PerceptionFrame] = None,
        command: Optional[ComposedCommand] = None,
        metrics: Optional[AssessmentMetrics] = None,
        feedback: Optional[FeedbackEvent] = None,
        device_mode: Optional[DeviceMode] = None,
        weights: Optional[Dict[str, float]] = None
    ) -> None:
        """Thread-safe update of live HUD telemetry data."""
        with self._lock:
            if perception is not None:
                self._current_perception = perception
            if command is not None:
                self._current_command = command
            if metrics is not None:
                self._current_metrics = metrics
            if feedback is not None:
                self._current_feedback = feedback
            if device_mode is not None:
                self._active_device_mode = device_mode
            if weights is not None:
                self._active_weights = dict(weights)

    def paintEvent(self, event) -> None:
        """Paints the explainability HUD components onto the transparent desktop canvas."""
        t0 = time.perf_counter()

        with self._lock:
            perc = self._current_perception
            cmd = self._current_command
            met = self._current_metrics
            fb = self._current_feedback
            mode = self._active_device_mode
            weights = dict(self._active_weights)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Top-Right Panel: System Health & Modality Status Card
        self._draw_health_status_card(painter, met, mode)

        # 2. Bottom-Right Panel: Per-Modality Confidence Breakdown Bars
        self._draw_confidence_breakdown_card(painter, perc, weights, cmd)

        # 3. Spatial Screen Target: Gaze Reticle & Tier-2 Dwell Confirmation Ring
        if perc is not None:
            self._draw_spatial_gaze_and_dwell(painter, perc, cmd)

        # 4. Top-Left Banner: Recent Supervisory Feedback Flash
        if fb is not None:
            self._draw_feedback_banner(painter, fb)

        self._last_paint_duration_ms = (time.perf_counter() - t0) * 1000.0

    def _draw_health_status_card(
        self,
        painter: QPainter,
        metrics: Optional[AssessmentMetrics],
        mode: DeviceMode
    ) -> None:
        """Renders top-right health badge and active device mode card."""
        x = self.screen_width - 320
        y = 20
        w = 300
        h = 100

        # Glassmorphic translucent card background
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        painter.setBrush(QBrush(QColor(15, 18, 24, 180)))
        painter.drawRoundedRect(QRectF(x, y, w, h), 10, 10)

        # Header Title
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.setPen(QColor(180, 190, 210, 220))
        painter.drawText(QRectF(x + 14, y + 10, w - 28, 18), Qt.AlignmentFlag.AlignLeft, "SYSTEM HEALTH & MODALITY")

        # Health state mapping
        health_str = metrics.health_state.value if metrics else "BOOTSTRAPPING"
        health_col = QColor(0, 255, 200, 230) # Default cyan
        if health_str == "LEARNING":
            health_col = QColor(255, 210, 0, 240)
        elif health_str == "STABLE":
            health_col = QColor(0, 255, 140, 240)
        elif health_str == "DRIFTING":
            health_col = QColor(255, 70, 70, 240)
        elif health_str == "IMPROVING":
            health_col = QColor(100, 220, 255, 240)

        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        painter.setPen(health_col)
        painter.drawText(QRectF(x + 14, y + 34, 160, 22), Qt.AlignmentFlag.AlignLeft, f"[{health_str}]")

        # Device Mode Pill
        mode_str = mode.value
        mode_col = QColor(120, 200, 255, 220) if mode == DeviceMode.GESTURE else QColor(255, 160, 60, 220)
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        painter.setPen(mode_col)
        painter.drawText(QRectF(x + 14, y + 64, w - 28, 20), Qt.AlignmentFlag.AlignLeft, f"MODE: {mode_str}")

        # WSI & ECE Metrics
        if metrics:
            wsi_val = metrics.weight_stability_index
            gain_val = metrics.adaptation_gain_ewma
            painter.setFont(QFont("Segoe UI", 9))
            painter.setPen(QColor(160, 170, 190, 200))
            painter.drawText(QRectF(x + 180, y + 36, 106, 18), Qt.AlignmentFlag.AlignRight, f"WSI: {wsi_val:.2f}")
            painter.drawText(QRectF(x + 180, y + 64, 106, 18), Qt.AlignmentFlag.AlignRight, f"GAIN: {gain_val:+.2f}")

    def _draw_confidence_breakdown_card(
        self,
        painter: QPainter,
        perc: Optional[PerceptionFrame],
        weights: Dict[str, float],
        cmd: Optional[ComposedCommand]
    ) -> None:
        """Renders bottom-right modality confidence breakdown bars."""
        w = 300
        h = 160
        x = self.screen_width - w - 20
        y = self.screen_height - h - 30

        # Background Card
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        painter.setBrush(QBrush(QColor(15, 18, 24, 180)))
        painter.drawRoundedRect(QRectF(x, y, w, h), 10, 10)

        # Title & Action
        action_name = cmd.action_type.value if cmd else "NO_ACTION"
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.setPen(QColor(180, 190, 210, 220))
        painter.drawText(QRectF(x + 14, y + 10, w - 28, 18), Qt.AlignmentFlag.AlignLeft, "MODALITY CONFIDENCE BREAKDOWN")

        action_col = QColor(0, 255, 140) if action_name != "NO_ACTION" else QColor(140, 150, 170)
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.setPen(action_col)
        painter.drawText(QRectF(x + 14, y + 30, w - 28, 18), Qt.AlignmentFlag.AlignLeft, f"ACTION: {action_name}")

        # Modal Channels: [Label, Confidence s_i, Weight w_i, Color]
        gaze_conf = perc.gaze_confidence if perc else 0.0
        head_conf = perc.head_confidence if perc else 0.0
        hand_conf = cmd.composed_score if cmd else 0.0

        channels = [
            ("GAZE", gaze_conf, weights.get("EYE", 0.40), QColor(0, 220, 255)),
            ("HEAD", head_conf, weights.get("HEAD", 0.30), QColor(255, 180, 0)),
            ("HAND", hand_conf, weights.get("HAND", 0.30), QColor(160, 100, 255))
        ]

        bar_x = x + 64
        bar_w = 160
        bar_h = 10
        start_y = y + 58

        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))

        for idx, (lbl, conf, wt, col) in enumerate(channels):
            by = start_y + (idx * 30)

            # Label
            painter.setPen(QColor(200, 210, 230, 220))
            painter.drawText(QRectF(x + 14, by - 2, 45, 16), Qt.AlignmentFlag.AlignLeft, lbl)

            # Bar track
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(40, 45, 60, 150)))
            painter.drawRoundedRect(QRectF(bar_x, by, bar_w, bar_h), 5, 5)

            # Bar fill (scaled by confidence)
            fill_w = max(4.0, bar_w * float(conf))
            painter.setBrush(QBrush(col))
            painter.drawRoundedRect(QRectF(bar_x, by, fill_w, bar_h), 5, 5)

            # Percentage & Weight text
            painter.setPen(QColor(220, 230, 245, 230))
            painter.drawText(QRectF(bar_x + bar_w + 8, by - 2, 60, 16), Qt.AlignmentFlag.AlignLeft, f"{int(conf*100)}% ({wt:.2f})")

    def _draw_spatial_gaze_and_dwell(
        self,
        painter: QPainter,
        perc: PerceptionFrame,
        cmd: Optional[ComposedCommand]
    ) -> None:
        """Renders live gaze reticle and Tier-2 dwell countdown confirmation ring."""
        gx, gy = perc.gaze_screen_xy
        if gx <= 0.0 and gy <= 0.0:
            return

        # 1. Gaze Reticle
        painter.setPen(QPen(QColor(0, 255, 140, 180), 1, Qt.PenStyle.SolidLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(gx, gy), 12, 12)
        painter.drawLine(int(gx - 18), int(gy), int(gx + 18), int(gy))
        painter.drawLine(int(gx), int(gy - 18), int(gx), int(gy + 18))

        # 2. Gaze Anchor & Tier-2 Dwell Ring
        if perc.gaze_anchor is not None:
            ax, ay = perc.gaze_anchor
            dwell_ms = perc.gaze_dwell_ms
            max_dwell_ms = 600.0
            dwell_progress = min(1.0, max(0.0, dwell_ms / max_dwell_ms))

            # Anchor circle
            painter.setPen(QPen(QColor(255, 220, 0, 200), 2))
            painter.drawEllipse(QPointF(ax, ay), 18, 18)

            # Tier-2 Progress Ring
            if dwell_progress > 0.05:
                ring_rect = QRectF(ax - 28, ay - 28, 56, 56)
                sweep_angle = int(-dwell_progress * 360 * 16) # 1/16th of a degree in Qt
                ring_col = QColor(0, 255, 140, 230) if dwell_progress >= 0.95 else QColor(255, 200, 0, 220)

                ring_pen = QPen(ring_col, 4)
                ring_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(ring_pen)
                painter.drawArc(ring_rect, 90 * 16, sweep_angle)

                # Dwell label
                painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                painter.setPen(ring_col)
                painter.drawText(QRectF(ax - 50, ay + 32, 100, 18), Qt.AlignmentFlag.AlignCenter, f"{int(dwell_ms)} ms")

    def _draw_feedback_banner(self, painter: QPainter, fb: FeedbackEvent) -> None:
        """Renders temporary top-left banner on supervisory feedback occurrence."""
        now = time.time()
        age_sec = now - fb.timestamp
        if age_sec > 3.0:
            return # Expired banner

        opacity = max(0.0, 1.0 - (age_sec / 3.0))
        is_pos = (fb.feedback_type.value == "IMPLICIT_POS")
        bg_col = QColor(0, 180, 80, int(180 * opacity)) if is_pos else QColor(220, 80, 20, int(190 * opacity))

        x = 20
        y = 20
        w = 340
        h = 44

        painter.setPen(QPen(QColor(255, 255, 255, int(60 * opacity)), 1))
        painter.setBrush(QBrush(bg_col))
        painter.drawRoundedRect(QRectF(x, y, w, h), 8, 8)

        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255, int(240 * opacity)))
        fb_title = f"FEEDBACK: {fb.feedback_type.value}"
        fb_sub = f"{fb.detector_source} -> {fb.failure_mode.value} (c: {fb.confidence_cfb:.2f})"
        painter.drawText(QRectF(x + 12, y + 6, w - 24, 16), Qt.AlignmentFlag.AlignLeft, fb_title)
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(QRectF(x + 12, y + 24, w - 24, 14), Qt.AlignmentFlag.AlignLeft, fb_sub)


__all__ = ["ExplainabilityHUDOverlay"]
