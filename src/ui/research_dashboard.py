"""
UI Subsystem: Master Empirical Research Dashboard Main Window.
Integrates live video perception feed, telemetry streaming, parameter evolution plotting,
Wald SPRT drift monitoring, counterbalanced Latin Square study execution, and automated statistical analysis.
Thread-safe architecture with main-thread GUI dispatch timer to guarantee zero freezing.
"""

from __future__ import annotations

import collections
import logging
import os
import sys
import threading
import time
from pathlib import Path
from typing import Deque, Dict, List, Optional, Tuple

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QImage, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.storage.schemas import (
    ActionContext,
    AssessmentMetrics,
    ComposedCommand,
    FeedbackEvent,
    GatekeeperDecision,
    GatekeeperVerdict,
    PerceptionFrame,
)
from src.ui.latin_square_panel import LatinSquarePanel
from src.ui.parameter_evolution_plot import ParameterEvolutionPlot
from src.ui.sprt_trajectory_gauge import SPRTTrajectoryGauge
from src.ui.telemetry_stream_viewer import TelemetryStreamViewer

logger = logging.getLogger(__name__)


class VideoFeedWidget(QWidget):
    """
    High-performance QPainter widget displaying the real-time annotated perception video feed.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(460, 340)
        self._current_image: Optional[QImage] = None
        self._lock = threading.Lock()

    def set_image(self, qimg: QImage) -> None:
        """Sets the current frame and triggers paint update."""
        with self._lock:
            self._current_image = qimg
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        painter.fillRect(rect, QColor(14, 17, 24))

        # Border
        painter.setPen(QColor(40, 50, 68))
        painter.drawRect(0, 0, rect.width() - 1, rect.height() - 1)

        with self._lock:
            img = self._current_image

        if img is not None and not img.isNull():
            scaled = img.scaled(
                rect.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation
            )
            ox = (rect.width() - scaled.width()) // 2
            oy = (rect.height() - scaled.height()) // 2
            painter.drawImage(ox, oy, scaled)
        else:
            painter.setPen(QColor(130, 150, 175))
            painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "Connecting Camera Stream (30 FPS)...")


class ResearchDashboardWindow(QMainWindow):
    """
    Empirical research control center window with thread-safe telemetry ingestion.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Multimodal HCI Empirical Research Dashboard & Diagnostics Suite")
        self.resize(1360, 860)

        # Thread-safe ingestion queues
        self._queue_lock = threading.Lock()
        self._latest_image: Optional[QImage] = None
        self._action_queue: Deque[ActionContext] = collections.deque(maxlen=100)
        self._feedback_queue: Deque[Tuple[FeedbackEvent, Optional[GatekeeperDecision], Optional[float]]] = collections.deque(maxlen=100)
        self._latest_metrics: Optional[Tuple[AssessmentMetrics, Optional[Dict[str, float]]]] = None

        self._setup_ui()
        self._setup_statusbar()

        # GUI Dispatch Timer (50 Hz / 20ms) executing strictly on Qt GUI Main Thread
        self._dispatch_timer = QTimer(self)
        self._dispatch_timer.timeout.connect(self._drain_event_queues)
        self._dispatch_timer.start(20)

    def _setup_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Header Title Bar
        header = QHBoxLayout()
        title_lbl = QLabel("Self-Evaluating Adaptive Multimodal HCI: Empirical Research Workstation")
        title_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #90CAF9; padding: 4px;")
        header.addWidget(title_lbl, stretch=1)

        self.lbl_system_status = QLabel("[STATUS: IDLE | ADAPTATION READY]")
        self.lbl_system_status.setStyleSheet("color: #00E676; font-weight: bold; padding: 4px;")
        header.addWidget(self.lbl_system_status)
        main_layout.addLayout(header)

        # Horizontal Splitter: Left (Live Video Feed) | Right (Multi-Tab Analytics)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # Left Container: Video Feed
        video_box = QWidget(self)
        vbox_left = QVBoxLayout(video_box)
        vbox_left.setContentsMargins(0, 0, 0, 0)
        lbl_v_title = QLabel("Live Perceptual Stream (FaceMesh, Irises & 21-pt Hands):")
        lbl_v_title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        lbl_v_title.setStyleSheet("color: #90CAF9;")

        self.video_feed = VideoFeedWidget(parent=self)
        vbox_left.addWidget(lbl_v_title)
        vbox_left.addWidget(self.video_feed, stretch=1)

        splitter.addWidget(video_box)

        # Right Container: Tab Widget
        self.tabs = QTabWidget(self)
        self.tabs.setFont(QFont("Segoe UI", 10))

        # Tab 1: Live Telemetry Stream
        self.tab_telemetry = TelemetryStreamViewer(parent=self)
        self.tabs.addTab(self.tab_telemetry, "1. Telemetry Stream")

        # Tab 2: Parameter & Simplex Evolution
        self.tab_params = ParameterEvolutionPlot(parent=self)
        self.tabs.addTab(self.tab_params, "2. Parameter Trajectory")

        # Tab 3: Wald SPRT Drift Monitor
        self.tab_sprt = SPRTTrajectoryGauge(parent=self)
        self.tabs.addTab(self.tab_sprt, "3. SPRT Drift Monitor")

        # Tab 4: Latin Square Study Runner
        self.tab_study = LatinSquarePanel(on_report_generated=self._on_study_report_generated, parent=self)
        self.tabs.addTab(self.tab_study, "4. Latin Square Study Runner")

        # Tab 5: Session Reports & LaTeX Synthesis
        self.tab_reports = QTextEdit(self)
        self.tab_reports.setReadOnly(True)
        self.tab_reports.setPlaceholderText("Generated Markdown session reports and LaTeX summary tables will display here...")
        self.tabs.addTab(self.tab_reports, "5. Statistical Reports")

        splitter.addWidget(self.tabs)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter, stretch=1)

    def _setup_statusbar(self) -> None:
        self.statusbar = QStatusBar(self)
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Research Dashboard initialized. Ready for empirical data collection.")

    def push_video_frame(self, qimg: QImage) -> None:
        """Thread-safe queue ingestion for video frame."""
        with self._queue_lock:
            self._latest_image = qimg

    def push_action_event(self, action: ActionContext) -> None:
        """Thread-safe queue ingestion of action execution event."""
        with self._queue_lock:
            self._action_queue.append(action)

    def push_feedback_event(
        self,
        fb: FeedbackEvent,
        verdict: Optional[GatekeeperDecision] = None,
        sprt_score: Optional[float] = None
    ) -> None:
        """Thread-safe queue ingestion of supervisory feedback event and SPRT verdict."""
        with self._queue_lock:
            self._feedback_queue.append((fb, verdict, sprt_score))

    def push_metrics_update(self, metrics: AssessmentMetrics, weights: Optional[Dict[str, float]] = None) -> None:
        """Thread-safe queue ingestion of health status and weight updates."""
        with self._queue_lock:
            self._latest_metrics = (metrics, weights)

    def _drain_event_queues(self) -> None:
        """
        Executed strictly on the Qt Main Thread at 50 Hz.
        Drains thread-safe queues and updates UI components with zero cross-thread blocking.
        """
        with self._queue_lock:
            img = self._latest_image
            self._latest_image = None

            actions = list(self._action_queue)
            self._action_queue.clear()

            feedbacks = list(self._feedback_queue)
            self._feedback_queue.clear()

            metrics_data = self._latest_metrics
            self._latest_metrics = None

        # 1. Update Video Feed
        if img is not None:
            self.video_feed.set_image(img)

        # 2. Process Actions
        for action in actions:
            self.tab_telemetry.record_action(action)
            if action.weights_snapshot:
                self.tab_params.update_weights(action.weights_snapshot, force=True)

        # 3. Process Feedback & SPRT
        for fb, verdict, sprt_score in feedbacks:
            self.tab_telemetry.record_feedback(fb, verdict)
            if sprt_score is not None:
                is_alarm = (verdict.verdict.value == "REJECT") if verdict else False
                self.tab_sprt.update_score(sprt_score, is_alarm=is_alarm)

        # 4. Update Metrics & Weights
        if metrics_data is not None:
            metrics, weights = metrics_data
            if weights:
                self.tab_params.update_weights(weights)
            status_text = f"[STATUS: {metrics.health_state.value} | WSI: {metrics.weight_stability_index:.2f} | GAIN: {metrics.adaptation_gain_ewma:+.2f}]"
            self.lbl_system_status.setText(status_text)

    def _on_study_report_generated(self, filepath: str) -> None:
        """Handles report generation callback from Latin Square panel."""
        try:
            with open(filepath, mode="r", encoding="utf-8") as f:
                content = f.read()
            self.tab_reports.setPlainText(content)
            self.tabs.setCurrentWidget(self.tab_reports)
            self.statusbar.showMessage(f"Session report saved: {os.path.basename(filepath)}", 5000)
        except Exception as e:
            logger.error("Failed to load generated report: %s", e)


__all__ = ["VideoFeedWidget", "ResearchDashboardWindow"]
