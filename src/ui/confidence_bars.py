"""
UI Subsystem: Modality Confidence Bars Renderer.
Computes layout geometry, dual-exponential smoothing, and color-coded contribution metrics.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen


class ConfidenceBarsRenderer:
    """
    Renders animated confidence meters for individual perceptual modalities.
    """

    def __init__(
        self,
        smoothing_alpha: float = 0.25,
        bar_width: float = 160.0,
        bar_height: float = 10.0
    ) -> None:
        self.smoothing_alpha = float(smoothing_alpha)
        self.bar_width = float(bar_width)
        self.bar_height = float(bar_height)

        # Smoothed values for [gaze, head, hand]
        self._smoothed_confs = [0.0, 0.0, 0.0]

    def update_values(self, gaze_conf: float, head_conf: float, hand_conf: float) -> List[float]:
        """Applies exponential smoothing to avoid visual jitter."""
        raws = [float(gaze_conf), float(head_conf), float(hand_conf)]
        for i in range(3):
            self._smoothed_confs[i] = (self.smoothing_alpha * raws[i]) + ((1.0 - self.smoothing_alpha) * self._smoothed_confs[i])
        return list(self._smoothed_confs)

    def render(
        self,
        painter: QPainter,
        origin_x: float,
        origin_y: float,
        gaze_conf: float,
        head_conf: float,
        hand_conf: float,
        weights: Dict[str, float],
        action_name: str = "NO_ACTION"
    ) -> None:
        """Draws the confidence breakdown card at specified origin coordinates."""
        confs = self.update_values(gaze_conf, head_conf, hand_conf)

        w = 300.0
        h = 160.0
        x, y = origin_x, origin_y

        # Background Card
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        painter.setBrush(QBrush(QColor(15, 18, 24, 180)))
        painter.drawRoundedRect(QRectF(x, y, w, h), 10, 10)

        # Title & Action
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.setPen(QColor(180, 190, 210, 220))
        painter.drawText(QRectF(x + 14, y + 10, w - 28, 18), Qt.AlignmentFlag.AlignLeft, "MODALITY CONFIDENCE BREAKDOWN")

        action_col = QColor(0, 255, 140) if action_name != "NO_ACTION" else QColor(140, 150, 170)
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.setPen(action_col)
        painter.drawText(QRectF(x + 14, y + 30, w - 28, 18), Qt.AlignmentFlag.AlignLeft, f"ACTION: {action_name}")

        channels = [
            ("GAZE", confs[0], weights.get("EYE", weights.get("GAZE", 0.40)), QColor(0, 220, 255)),
            ("HEAD", confs[1], weights.get("HEAD", 0.30), QColor(255, 180, 0)),
            ("HAND", confs[2], weights.get("HAND", weights.get("GESTURE", 0.30)), QColor(160, 100, 255))
        ]

        bar_x = x + 64
        start_y = y + 58

        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))

        for idx, (lbl, conf, wt, col) in enumerate(channels):
            by = start_y + (idx * 30)

            # Label
            painter.setPen(QColor(200, 210, 230, 220))
            painter.drawText(QRectF(x + 14, by - 2, 45, 16), Qt.AlignmentFlag.AlignLeft, lbl)

            # Track
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(40, 45, 60, 150)))
            painter.drawRoundedRect(QRectF(bar_x, by, self.bar_width, self.bar_height), 5, 5)

            # Fill
            fill_w = max(4.0, self.bar_width * float(conf))
            painter.setBrush(QBrush(col))
            painter.drawRoundedRect(QRectF(bar_x, by, fill_w, self.bar_height), 5, 5)

            # Percentage & Weight text
            painter.setPen(QColor(220, 230, 245, 230))
            painter.drawText(QRectF(bar_x + self.bar_width + 8, by - 2, 60, 16), Qt.AlignmentFlag.AlignLeft, f"{int(conf*100)}% ({wt:.2f})")


__all__ = ["ConfidenceBarsRenderer"]
