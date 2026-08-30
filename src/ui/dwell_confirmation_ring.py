"""
UI Subsystem: Spatial Dwell Confirmation Ring.
Renders circular progress countdown rings for Tier-2 high-consequence actions at gaze anchor locations.
"""

from __future__ import annotations

import math
from typing import Optional, Tuple
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen


class DwellConfirmationRing:
    """
    Renders an animated circular countdown progress ring centered on the active gaze anchor.
    """

    def __init__(
        self,
        dwell_confirmation_threshold_ms: float = 600.0,
        ring_radius: float = 28.0,
        ring_stroke_width: float = 4.0
    ) -> None:
        self.dwell_confirmation_threshold_ms = float(dwell_confirmation_threshold_ms)
        self.ring_radius = float(ring_radius)
        self.ring_stroke_width = float(ring_stroke_width)

    def calculate_sweep_angle(self, dwell_ms: float) -> Tuple[float, float]:
        """
        Calculates normalized progress in [0.0, 1.0] and angular sweep in degrees.

        Returns:
            Tuple of (progress_ratio, sweep_angle_degrees).
        """
        prog = min(1.0, max(0.0, float(dwell_ms) / self.dwell_confirmation_threshold_ms))
        sweep = 360.0 * prog
        return prog, sweep

    def render(
        self,
        painter: QPainter,
        anchor_xy: Tuple[float, float],
        dwell_ms: float
    ) -> None:
        """Draws the confirmation ring at the anchor position."""
        ax, ay = anchor_xy
        prog, sweep_deg = self.calculate_sweep_angle(dwell_ms)

        # 1. Base anchor center ring
        painter.setPen(QPen(QColor(255, 220, 0, 200), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(ax, ay), 16, 16)

        # 2. Outer Progress Arc
        if prog > 0.02:
            r = self.ring_radius
            ring_rect = QRectF(ax - r, ay - r, 2 * r, 2 * r)

            # Color: transitions from warm yellow to bright locked green at 100%
            ring_col = QColor(0, 255, 140, 230) if prog >= 0.95 else QColor(255, 200, 0, 220)

            pen = QPen(ring_col, self.ring_stroke_width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)

            # Qt drawArc expects angles in 1/16th of a degree, starting from 90° (top)
            start_angle = 90 * 16
            span_angle = int(-sweep_deg * 16)
            painter.drawArc(ring_rect, start_angle, span_angle)

            # Countdown text label
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            painter.setPen(ring_col)
            label = "CONFIRMED" if prog >= 1.0 else f"{int(dwell_ms)} ms"
            painter.drawText(QRectF(ax - 50, ay + r + 4, 100, 18), Qt.AlignmentFlag.AlignCenter, label)


__all__ = ["DwellConfirmationRing"]
