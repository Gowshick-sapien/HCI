"""
UI Subsystem: System Health Badge & Modality Handoff Renderer.
Renders color-coded status badges for Layer 5 Health States, Macro Policies, and Device Modes.
"""

from __future__ import annotations

from typing import Optional, Tuple
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen

from src.storage.schemas import (
    AssessmentMetrics,
    DeviceMode,
    MacroPolicy,
    SystemHealthState,
)


class HealthBadgeRenderer:
    """
    Renders system health state badge, WSI stability gauge, and macro policy indicators.
    """

    @staticmethod
    def get_health_palette(state: SystemHealthState) -> Tuple[QColor, str]:
        """Maps health state to display string and QColor."""
        if state == SystemHealthState.BOOTSTRAPPING:
            return QColor(140, 150, 170, 230), "BOOTSTRAPPING"
        elif state == SystemHealthState.LEARNING:
            return QColor(255, 210, 0, 240), "LEARNING"
        elif state == SystemHealthState.IMPROVING:
            return QColor(100, 220, 255, 240), "IMPROVING"
        elif state == SystemHealthState.STABLE:
            return QColor(0, 255, 140, 240), "STABLE"
        elif state == SystemHealthState.DRIFTING:
            return QColor(255, 70, 70, 240), "DRIFTING"
        elif state == SystemHealthState.RECOVERING:
            return QColor(255, 140, 0, 240), "RECOVERING"
        return QColor(140, 150, 170, 230), "UNKNOWN"

    @staticmethod
    def get_device_mode_palette(mode: DeviceMode) -> Tuple[QColor, str]:
        """Maps device mode to display string and QColor."""
        if mode == DeviceMode.GESTURE:
            return QColor(120, 200, 255, 220), "GESTURE [ACTIVE]"
        elif mode == DeviceMode.MOUSE_PRIORITY:
            return QColor(255, 160, 60, 220), "MOUSE [PRIORITY]"
        elif mode == DeviceMode.KEYBOARD:
            return QColor(255, 100, 100, 220), "KEYBOARD [ACTIVE]"
        elif mode == DeviceMode.NO_ACTION:
            return QColor(180, 180, 180, 220), "NO_ACTION"
        return QColor(180, 180, 180, 220), mode.value

    def render(
        self,
        painter: QPainter,
        origin_x: float,
        origin_y: float,
        metrics: Optional[AssessmentMetrics],
        mode: DeviceMode = DeviceMode.GESTURE,
        policy: MacroPolicy = MacroPolicy.MERGE
    ) -> None:
        """Renders health and device mode card at origin."""
        w = 300.0
        h = 100.0
        x, y = origin_x, origin_y

        # Card container
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        painter.setBrush(QBrush(QColor(15, 18, 24, 180)))
        painter.drawRoundedRect(QRectF(x, y, w, h), 10, 10)

        # Header Title
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.setPen(QColor(180, 190, 210, 220))
        painter.drawText(QRectF(x + 14, y + 10, w - 28, 18), Qt.AlignmentFlag.AlignLeft, "SYSTEM HEALTH & MODALITY")

        # Health state badge
        health_state = metrics.health_state if metrics else SystemHealthState.BOOTSTRAPPING
        col, label = self.get_health_palette(health_state)

        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        painter.setPen(col)
        painter.drawText(QRectF(x + 14, y + 34, 160, 22), Qt.AlignmentFlag.AlignLeft, f"[{label}]")

        # Device mode pill
        m_col, m_lbl = self.get_device_mode_palette(mode)
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        painter.setPen(m_col)
        painter.drawText(QRectF(x + 14, y + 64, w - 28, 20), Qt.AlignmentFlag.AlignLeft, f"MODE: {m_lbl}")

        # Metrics text
        if metrics:
            painter.setFont(QFont("Segoe UI", 9))
            painter.setPen(QColor(160, 170, 190, 200))
            painter.drawText(QRectF(x + 180, y + 36, 106, 18), Qt.AlignmentFlag.AlignRight, f"WSI: {metrics.weight_stability_index:.2f}")
            painter.drawText(QRectF(x + 180, y + 64, 106, 18), Qt.AlignmentFlag.AlignRight, f"GAIN: {metrics.adaptation_gain_ewma:+.2f}")


__all__ = ["HealthBadgeRenderer"]
