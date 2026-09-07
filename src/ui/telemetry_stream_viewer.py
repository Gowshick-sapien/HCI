"""
UI Subsystem: Real-Time Telemetry Stream Viewer.
Renders a live scrolling table of ActionContext, FeedbackEvent, and Gatekeeper decisions
with search filtering and one-click JSON/CSV dataset export.
"""

from __future__ import annotations

import collections
import datetime
import json
from typing import Deque, Dict, List, Optional

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from src.storage.schemas import ActionContext, FeedbackEvent, GatekeeperDecision, GatekeeperVerdict


class TelemetryTableModel(QAbstractTableModel):
    """Table model backing the live streaming telemetry viewer."""

    HEADERS = ["Time", "Event Type", "Source / Action", "Outcome / Status", "Latency (s)", "Confidence", "Weights / Details"]

    def __init__(self, max_rows: int = 500, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.max_rows = max_rows
        self._all_records: Deque[Dict[str, str]] = collections.deque(maxlen=max_rows)
        self._filtered_records: List[Dict[str, str]] = []
        self._current_filter: str = ""

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._filtered_records)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._filtered_records)):
            return None

        row_data = self._filtered_records[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            keys = ["time", "event_type", "source_action", "outcome", "latency", "confidence", "details"]
            return row_data.get(keys[col], "")
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (0, 4, 5):
                return int(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self.HEADERS):
                return self.HEADERS[section]
        return None

    def add_action_record(self, action: ActionContext) -> None:
        """Appends a new ActionContext record."""
        ts_str = datetime.datetime.fromtimestamp(action.timestamp_t0).strftime("%H:%M:%S.%f")[:-3]
        w = action.weights_snapshot or {}
        w_str = f"EYE:{w.get('EYE', 0.4):.2f}, HEAD:{w.get('HEAD', 0.3):.2f}, HAND:{w.get('HAND', 0.3):.2f}"
        rec = {
            "time": ts_str,
            "event_type": "ACTION_DISPATCH",
            "source_action": action.action_name,
            "outcome": "EXECUTED" if action.is_executed else "PENDING",
            "latency": "-",
            "confidence": f"{action.fused_score:.2f}",
            "details": f"Tier: {action.tier.value} | {w_str}"
        }
        self._insert_record(rec)

    def add_feedback_record(self, fb: FeedbackEvent, verdict: Optional[GatekeeperVerdict] = None) -> None:
        """Appends a supervisory FeedbackEvent record."""
        ts_str = datetime.datetime.fromtimestamp(fb.timestamp).strftime("%H:%M:%S.%f")[:-3]
        v_str = f"Gatekeeper: {verdict.verdict.value}" if verdict else "Gatekeeper: PENDING"
        rec = {
            "time": ts_str,
            "event_type": fb.feedback_type.value,
            "source_action": f"{fb.detector_source} -> {fb.action_id}",
            "outcome": fb.failure_mode.value,
            "latency": f"{fb.latency_delta_t:.2f}",
            "confidence": f"{fb.confidence_cfb:.2f}",
            "details": f"{v_str} | Severity: {fb.severity.value}"
        }
        self._insert_record(rec)

    def _insert_record(self, rec: Dict[str, str]) -> None:
        self.beginResetModel()
        self._all_records.appendleft(rec)
        self._apply_filter_internal()
        self.endResetModel()

    def set_filter(self, query: str) -> None:
        """Filters rows containing the query string."""
        self.beginResetModel()
        self._current_filter = query.strip().lower()
        self._apply_filter_internal()
        self.endResetModel()

    def _apply_filter_internal(self) -> None:
        if not self._current_filter:
            self._filtered_records = list(self._all_records)
        else:
            q = self._current_filter
            self._filtered_records = [
                r for r in self._all_records
                if any(q in str(v).lower() for v in r.values())
            ]

    def clear(self) -> None:
        self.beginResetModel()
        self._all_records.clear()
        self._filtered_records.clear()
        self.endResetModel()


class TelemetryStreamViewer(QWidget):
    """
    GUI Widget embedding the live telemetry table with search box and controls.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Top Control Bar
        ctrl_bar = QHBoxLayout()
        lbl_search = QLabel("Filter Telemetry:")
        self.edit_search = QLineEdit()
        self.edit_search.setPlaceholderText("Search action, failure mode, or feedback type...")
        self.edit_search.textChanged.connect(self._on_search_changed)

        btn_clear = QPushButton("Clear Stream")
        btn_clear.clicked.connect(self._on_clear_clicked)

        ctrl_bar.addWidget(lbl_search)
        ctrl_bar.addWidget(self.edit_search, stretch=1)
        ctrl_bar.addWidget(btn_clear)
        layout.addLayout(ctrl_bar)

        # Table View
        self.model = TelemetryTableModel(max_rows=500, parent=self)
        self.table_view = QTableView(self)
        self.table_view.setModel(self.model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.setAlternatingRowColors(True)
        layout.addWidget(self.table_view, stretch=1)

    def _on_search_changed(self, text: str) -> None:
        self.model.set_filter(text)

    def _on_clear_clicked(self) -> None:
        self.model.clear()

    def record_action(self, action: ActionContext) -> None:
        self.model.add_action_record(action)

    def record_feedback(self, fb: FeedbackEvent, verdict: Optional[GatekeeperVerdict] = None) -> None:
        self.model.add_feedback_record(fb, verdict)


__all__ = ["TelemetryTableModel", "TelemetryStreamViewer"]
