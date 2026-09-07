"""
UI Subsystem: Wald SPRT Drift & Hypothesis Gauge.
Renders real-time Sequential Probability Ratio Test log-likelihood trajectory curves,
decision thresholds (A = 2.89, B = -2.25), and gatekeeper alarm badges.
"""

from __future__ import annotations

import collections
from typing import Deque, List, Optional

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class SPRTTrajectoryCanvas(QWidget):
    """
    Renders rolling SPRT log-likelihood ratio Lambda_n history and decision boundaries.
    """

    def __init__(
        self,
        threshold_a: float = 2.89,
        threshold_b: float = -2.25,
        max_history: int = 100,
        parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.threshold_a = float(threshold_a)
        self.threshold_b = float(threshold_b)
        self.max_history = max(30, int(max_history))
        self.setMinimumHeight(220)

        self._sprt_history: Deque[float] = collections.deque(maxlen=self.max_history)
        self._current_score: float = 0.0
        self._alarm_active: bool = False

        # Pre-seed with zero
        for _ in range(5):
            self._sprt_history.append(0.0)

    def push_score(self, score: float, is_alarm: bool = False) -> None:
        """Appends a new cumulative log-likelihood score."""
        self._current_score = float(score)
        self._alarm_active = bool(is_alarm)
        self._sprt_history.append(self._current_score)
        self.update()

    def reset(self) -> None:
        """Resets the history and current score to baseline."""
        self._sprt_history.clear()
        self._current_score = 0.0
        self._alarm_active = False
        for _ in range(5):
            self._sprt_history.append(0.0)
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        w, h = rect.width(), rect.height()
        pad_left, pad_right = 50.0, 30.0
        pad_top, pad_bottom = 30.0, 30.0

        plot_w = max(10.0, w - pad_left - pad_right)
        plot_h = max(10.0, h - pad_top - pad_bottom)

        # Plot range: from -4.0 to +4.0
        min_val, max_val = -4.0, 4.0
        val_range = max_val - min_val

        def val_to_y(v: float) -> float:
            norm = (v - min_val) / val_range
            return pad_top + plot_h - (norm * plot_h)

        # Canvas background
        painter.setPen(QPen(QColor(60, 65, 80), 1))
        painter.setBrush(QBrush(QColor(20, 24, 32)))
        painter.drawRoundedRect(QRectF(pad_left, pad_top, plot_w, plot_h), 6, 6)

        # Draw Grid & Threshold Boundaries
        # 1. Zero Baseline
        y_zero = val_to_y(0.0)
        painter.setPen(QPen(QColor(80, 90, 110), 1, Qt.PenStyle.SolidLine))
        painter.drawLine(int(pad_left), int(y_zero), int(pad_left + plot_w), int(y_zero))

        # 2. Upper Decision Boundary A = +2.89 (APPROVE / DRIFT ALARM)
        y_a = val_to_y(self.threshold_a)
        painter.setPen(QPen(QColor(255, 80, 80), 1.5, Qt.PenStyle.DashLine))
        painter.drawLine(int(pad_left), int(y_a), int(pad_left + plot_w), int(y_a))

        # 3. Lower Decision Boundary B = -2.25 (NOISE RESET)
        y_b = val_to_y(self.threshold_b)
        painter.setPen(QPen(QColor(0, 220, 140), 1.5, Qt.PenStyle.DashLine))
        painter.drawLine(int(pad_left), int(y_b), int(pad_left + plot_w), int(y_b))

        # Axis labels
        painter.setFont(QFont("Segoe UI", 8))
        for v in [-2.25, 0.0, 2.89]:
            y_pos = val_to_y(v)
            painter.setPen(QColor(160, 170, 190))
            painter.drawText(QRectF(0, y_pos - 8, pad_left - 8, 16), Qt.AlignmentFlag.AlignRight, f"{v:+.2f}")

        # Text labels on boundaries
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        painter.setPen(QColor(255, 100, 100))
        painter.drawText(QRectF(pad_left + 8, y_a - 18, 250, 16), Qt.AlignmentFlag.AlignLeft, f"Upper Bound A = {self.threshold_a:.2f} (Approve Update / Drift)")
        painter.setPen(QColor(0, 220, 140))
        painter.drawText(QRectF(pad_left + 8, y_b + 4, 250, 16), Qt.AlignmentFlag.AlignLeft, f"Lower Bound B = {self.threshold_b:.2f} (Accept Noise / Reset)")

        # Draw SPRT Trajectory Line
        pts = list(self._sprt_history)
        n_pts = len(pts)
        if n_pts > 1:
            dx = plot_w / (self.max_history - 1)
            x_offset = pad_left + (self.max_history - n_pts) * dx

            path = QPainterPath()
            for i, val in enumerate(pts):
                px = x_offset + (i * dx)
                py = val_to_y(val)
                if i == 0:
                    path.moveTo(px, py)
                else:
                    path.lineTo(px, py)

            line_color = QColor(255, 70, 70) if self._alarm_active else QColor(100, 200, 255)
            painter.setPen(QPen(line_color, 2.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)

        # Header Score Info
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        status_str = "ALARM: DRIFT DETECTED" if self._alarm_active else "SPRT STATUS: STABLE"
        status_col = QColor(255, 70, 70) if self._alarm_active else QColor(0, 255, 140)

        painter.setPen(QColor(200, 210, 230))
        painter.drawText(QRectF(pad_left, 6, 260, 20), Qt.AlignmentFlag.AlignLeft, f"Wald SPRT Accumulator: Lambda_n = {self._current_score:+.3f}")

        painter.setPen(status_col)
        painter.drawText(QRectF(pad_left + plot_w - 200, 6, 200, 20), Qt.AlignmentFlag.AlignRight, f"[{status_str}]")


class SPRTTrajectoryGauge(QWidget):
    """
    Container widget embedding the SPRT canvas and reset controls.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        header = QHBoxLayout()
        lbl_info = QLabel("Sequential Hypothesis Drift Testing (H0: Noise vs. H1: Systematic Bias):")
        btn_reset = QPushButton("Reset SPRT Gauge")
        btn_reset.clicked.connect(self._on_reset)

        header.addWidget(lbl_info, stretch=1)
        header.addWidget(btn_reset)
        layout.addLayout(header)

        self.canvas = SPRTTrajectoryCanvas(parent=self)
        layout.addWidget(self.canvas, stretch=1)

    def _on_reset(self) -> None:
        self.canvas.reset()

    def update_score(self, score: float, is_alarm: bool = False) -> None:
        self.canvas.push_score(score, is_alarm)


__all__ = ["SPRTTrajectoryCanvas", "SPRTTrajectoryGauge"]
