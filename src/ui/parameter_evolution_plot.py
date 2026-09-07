"""
UI Subsystem: Parameter & Simplex Evolution Visualizer.
Renders real-time trajectory curves for modality weights (EYE, HEAD, HAND)
along with probability simplex boundaries, live numerical meters, and interactive diagnostics.
"""

from __future__ import annotations

import collections
import time
from typing import Deque, Dict, List, Optional, Tuple

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ParameterEvolutionCanvas(QWidget):
    """
    High-performance QPainter canvas plotting modality weight curves over time.
    """

    def __init__(self, max_history: int = 200, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.max_history = max(50, int(max_history))
        self.setMinimumHeight(280)

        self._eye_history: Deque[float] = collections.deque(maxlen=self.max_history)
        self._head_history: Deque[float] = collections.deque(maxlen=self.max_history)
        self._hand_history: Deque[float] = collections.deque(maxlen=self.max_history)

        self._last_push_time: float = 0.0
        self._last_weights: Dict[str, float] = {"EYE": 0.40, "HEAD": 0.30, "HAND": 0.30}

        # Baseline initialization
        for _ in range(15):
            self.push_weights({"EYE": 0.40, "HEAD": 0.30, "HAND": 0.30}, force=True)

    def push_weights(self, weights: Dict[str, float], force: bool = False) -> None:
        """
        Appends a new weight vector snapshot to the history.
        Throttles identical weights to avoid filling the buffer within 5 seconds at 30 FPS.
        """
        now = time.time()
        w_eye = float(weights.get("EYE", 0.40))
        w_head = float(weights.get("HEAD", 0.30))
        w_hand = float(weights.get("HAND", 0.30))

        # Check if weights shifted or 0.8s elapsed
        has_changed = (
            abs(w_eye - self._last_weights.get("EYE", 0.40)) > 0.001 or
            abs(w_head - self._last_weights.get("HEAD", 0.30)) > 0.001 or
            abs(w_hand - self._last_weights.get("HAND", 0.30)) > 0.001
        )

        if force or has_changed or (now - self._last_push_time >= 0.80):
            self._eye_history.append(w_eye)
            self._head_history.append(w_head)
            self._hand_history.append(w_hand)
            self._last_weights = {"EYE": w_eye, "HEAD": w_head, "HAND": w_hand}
            self._last_push_time = now
            self.update()

    def clear_history(self) -> None:
        """Resets the plotting history."""
        self._eye_history.clear()
        self._head_history.clear()
        self._hand_history.clear()
        for _ in range(15):
            self.push_weights({"EYE": 0.40, "HEAD": 0.30, "HAND": 0.30}, force=True)
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        w, h = rect.width(), rect.height()
        pad_left, pad_right = 55.0, 30.0
        pad_top, pad_bottom = 35.0, 35.0

        plot_w = max(10.0, w - pad_left - pad_right)
        plot_h = max(10.0, h - pad_top - pad_bottom)

        # Background canvas
        painter.setPen(QPen(QColor(45, 52, 65), 1))
        painter.setBrush(QBrush(QColor(16, 20, 28)))
        painter.drawRoundedRect(QRectF(pad_left, pad_top, plot_w, plot_h), 6, 6)

        # Grid lines (0.05, 0.20, 0.40, 0.60, 0.80, 0.85)
        painter.setFont(QFont("Segoe UI", 8))
        for step in [0.05, 0.20, 0.40, 0.60, 0.80, 0.85]:
            gy = pad_top + plot_h - (step * plot_h)
            is_bound = (step in (0.05, 0.85))
            grid_pen = QPen(QColor(255, 90, 90, 140) if is_bound else QColor(40, 48, 62), 1, Qt.PenStyle.DashLine if is_bound else Qt.PenStyle.SolidLine)
            painter.setPen(grid_pen)
            painter.drawLine(int(pad_left), int(gy), int(pad_left + plot_w), int(gy))

            # Y-axis label
            painter.setPen(QColor(160, 170, 190))
            painter.drawText(QRectF(0, gy - 8, pad_left - 8, 16), Qt.AlignmentFlag.AlignRight, f"{step:.2f}")

        # Simplex limits text
        painter.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        painter.setPen(QColor(255, 110, 110, 180))
        painter.drawText(QRectF(pad_left + 8, pad_top + 4, 180, 14), Qt.AlignmentFlag.AlignLeft, "Upper Box Constraint u_i = 0.85")
        painter.drawText(QRectF(pad_left + 8, pad_top + plot_h - 18, 180, 14), Qt.AlignmentFlag.AlignLeft, "Lower Box Constraint l_i = 0.05")

        # Draw weight trajectory curves
        channels = [
            ("EYE (Gaze)", list(self._eye_history), QColor(0, 220, 255)),
            ("HEAD (Pose)", list(self._head_history), QColor(255, 180, 0)),
            ("HAND (Gesture)", list(self._hand_history), QColor(180, 100, 255))
        ]

        n_pts = len(self._eye_history)
        if n_pts > 1:
            dx = plot_w / (self.max_history - 1)
            x_offset = pad_left + (self.max_history - n_pts) * dx

            for name, hist, color in channels:
                path = QPainterPath()
                for i, val in enumerate(hist):
                    px = x_offset + (i * dx)
                    py = pad_top + plot_h - (val * plot_h)
                    if i == 0:
                        path.moveTo(px, py)
                    else:
                        path.lineTo(px, py)

                painter.setPen(QPen(color, 2.5))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPath(path)

                # Draw point marker at the latest value
                if len(hist) > 0:
                    latest_val = hist[-1]
                    lx = x_offset + ((len(hist) - 1) * dx)
                    ly = pad_top + plot_h - (latest_val * plot_h)
                    painter.setPen(QPen(QColor(255, 255, 255), 1.5))
                    painter.setBrush(QBrush(color))
                    painter.drawEllipse(QPointF(lx, ly), 4.5, 4.5)

        # Legend Header
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.setPen(QColor(200, 210, 230))
        painter.drawText(QRectF(pad_left, 6, 260, 20), Qt.AlignmentFlag.AlignLeft, "Modality Weight Evolution: w(t) in Simplex")

        leg_x = pad_left + plot_w - 280
        for name, _, col in channels:
            painter.setPen(col)
            painter.drawText(QRectF(leg_x, 6, 90, 20), Qt.AlignmentFlag.AlignLeft, name.split()[0])
            leg_x += 95


class ParameterEvolutionPlot(QWidget):
    """
    Container widget embedding the parameter evolution canvas, live digital readouts, and controls.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 1. Top Live Numerical Readouts
        readouts_frame = QFrame()
        readouts_frame.setStyleSheet("background-color: #141824; border: 1px solid #283040; border-radius: 6px; padding: 6px;")
        grid = QGridLayout(readouts_frame)
        grid.setContentsMargins(8, 4, 8, 4)

        self.lbl_eye_val = QLabel("EYE: 0.40")
        self.lbl_eye_val.setStyleSheet("font-size: 13px; font-weight: bold; color: #00E5FF;")
        self.lbl_head_val = QLabel("HEAD: 0.30")
        self.lbl_head_val.setStyleSheet("font-size: 13px; font-weight: bold; color: #FFD600;")
        self.lbl_hand_val = QLabel("HAND: 0.30")
        self.lbl_hand_val.setStyleSheet("font-size: 13px; font-weight: bold; color: #D500F9;")
        self.lbl_sum_val = QLabel("Simplex Sum: 1.000 (Valid)")
        self.lbl_sum_val.setStyleSheet("font-size: 12px; font-weight: bold; color: #00E676;")

        grid.addWidget(QLabel("Current Modality Weights:"), 0, 0)
        grid.addWidget(self.lbl_eye_val, 0, 1)
        grid.addWidget(self.lbl_head_val, 0, 2)
        grid.addWidget(self.lbl_hand_val, 0, 3)
        grid.addWidget(self.lbl_sum_val, 0, 4)
        layout.addWidget(readouts_frame)

        # 2. Main Trajectory Canvas
        self.canvas = ParameterEvolutionCanvas(max_history=200, parent=self)
        layout.addWidget(self.canvas, stretch=1)

        # 3. Interactive Diagnostic Controls
        ctrl_box = QGroupBox("Interactive Micro-Adaptation Testing Controls")
        hbox_ctrl = QHBoxLayout(ctrl_box)

        btn_boost_eye = QPushButton("+5% Gaze Weight")
        btn_boost_eye.clicked.connect(lambda: self._simulate_boost("EYE"))

        btn_boost_head = QPushButton("+5% Head Weight")
        btn_boost_head.clicked.connect(lambda: self._simulate_boost("HEAD"))

        btn_boost_hand = QPushButton("+5% Hand Weight")
        btn_boost_hand.clicked.connect(lambda: self._simulate_boost("HAND"))

        btn_reset = QPushButton("Reset to Baseline (0.40, 0.30, 0.30)")
        btn_reset.clicked.connect(self._on_reset)

        hbox_ctrl.addWidget(btn_boost_eye)
        hbox_ctrl.addWidget(btn_boost_head)
        hbox_ctrl.addWidget(btn_boost_hand)
        hbox_ctrl.addWidget(btn_reset)
        layout.addWidget(ctrl_box)

    def _simulate_boost(self, target_modality: str) -> None:
        """Simulates a micro-adaptation gradient update step on the simplex."""
        curr = dict(self.canvas._last_weights)
        boost = 0.05
        other_deduct = boost / 2.0

        if target_modality == "EYE":
            curr["EYE"] = min(0.85, curr.get("EYE", 0.40) + boost)
            curr["HEAD"] = max(0.05, curr.get("HEAD", 0.30) - other_deduct)
            curr["HAND"] = max(0.05, curr.get("HAND", 0.30) - other_deduct)
        elif target_modality == "HEAD":
            curr["HEAD"] = min(0.85, curr.get("HEAD", 0.30) + boost)
            curr["EYE"] = max(0.05, curr.get("EYE", 0.40) - other_deduct)
            curr["HAND"] = max(0.05, curr.get("HAND", 0.30) - other_deduct)
        elif target_modality == "HAND":
            curr["HAND"] = min(0.85, curr.get("HAND", 0.30) + boost)
            curr["EYE"] = max(0.05, curr.get("EYE", 0.40) - other_deduct)
            curr["HEAD"] = max(0.05, curr.get("HEAD", 0.30) - other_deduct)

        # Normalize sum to 1.0
        total = curr["EYE"] + curr["HEAD"] + curr["HAND"]
        for k in curr:
            curr[k] /= total

        self.update_weights(curr, force=True)

    def _on_reset(self) -> None:
        self.canvas.clear_history()
        self.update_weights({"EYE": 0.40, "HEAD": 0.30, "HAND": 0.30}, force=True)

    def update_weights(self, weights: Dict[str, float], force: bool = False) -> None:
        """Pushes new weights to canvas and updates digital readout labels."""
        w_eye = weights.get("EYE", 0.40)
        w_head = weights.get("HEAD", 0.30)
        w_hand = weights.get("HAND", 0.30)
        total = w_eye + w_head + w_hand

        self.lbl_eye_val.setText(f"EYE: {w_eye:.2f}")
        self.lbl_head_val.setText(f"HEAD: {w_head:.2f}")
        self.lbl_hand_val.setText(f"HAND: {w_hand:.2f}")

        is_valid = abs(total - 1.0) < 1e-3 and (0.05 <= w_eye <= 0.85) and (0.05 <= w_head <= 0.85) and (0.05 <= w_hand <= 0.85)
        sum_str = f"Simplex Sum: {total:.3f} ({'Valid' if is_valid else 'Out-of-Bounds'})"
        sum_col = "#00E676" if is_valid else "#FF1744"
        self.lbl_sum_val.setText(sum_str)
        self.lbl_sum_val.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {sum_col};")

        self.canvas.push_weights(weights, force=force)


__all__ = ["ParameterEvolutionCanvas", "ParameterEvolutionPlot"]
