"""
Unit tests for TelemetryStreamViewer (Deliverable E3).
Verifies Invariant INV-E3.2: Table model insertion, text formatting, and query filtering.
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
from PySide6.QtWidgets import QApplication

from src.storage.schemas import (
    ActionContext,
    ActionTier,
    FailureMode,
    FailureSeverity,
    FeedbackEvent,
    FeedbackType,
    GatekeeperDecision,
    GatekeeperVerdict,
)
from src.ui.telemetry_stream_viewer import TelemetryStreamViewer, TelemetryTableModel


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_telemetry_table_model_insertion_and_filtering(qapp):
    """Invariant INV-E3.2: Telemetry table inserts records and filters correctly."""
    model = TelemetryTableModel(max_rows=50)

    action = ActionContext(
        action_id="act_001",
        action_name="PRIMARY_CLICK",
        tier=ActionTier.TIER_1_IMMEDIATE,
        timestamp_t0=time.time(),
        target_pid=1234,
        target_window_title="Test App",
        feature_snapshot=None,
        weights_snapshot={"EYE": 0.4, "HEAD": 0.3, "HAND": 0.3},
        fused_score=0.88,
        threshold=0.70,
        is_executed=True
    )

    fb = FeedbackEvent(
        feedback_id="fb_001",
        action_id="act_001",
        timestamp=time.time(),
        latency_delta_t=0.45,
        feedback_type=FeedbackType.IMPLICIT_NEG,
        confidence_cfb=0.82,
        failure_mode=FailureMode.USER_OVERRIDE,
        severity=FailureSeverity.SEV_2_MINOR,
        detector_source="IMPLICIT_MOUSE_TAKEOVER"
    )

    model.add_action_record(action)
    model.add_feedback_record(fb)

    assert model.rowCount() == 2
    assert model.columnCount() == 7

    # Test query filter: search "PRIMARY_CLICK" -> 1 match
    model.set_filter("PRIMARY_CLICK")
    assert model.rowCount() == 1

    # Search "USER_OVERRIDE" -> 1 match
    model.set_filter("USER_OVERRIDE")
    assert model.rowCount() == 1

    # Search non-existent -> 0 matches
    model.set_filter("NON_EXISTENT_TOKEN")
    assert model.rowCount() == 0

    # Clear filter -> 2 matches
    model.set_filter("")
    assert model.rowCount() == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
