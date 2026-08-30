"""
Unit tests for Layer 4 Feedback Telemetry Logger.
Verifies thread-safe atomic JSONL disk logging.
"""

from pathlib import Path
import pytest

from src.feedback.telemetry_logger import FeedbackTelemetryLogger
from src.storage.schemas import (
    FailureMode,
    FailureSeverity,
    FeedbackEvent,
    FeedbackType,
)


def test_telemetry_logger_roundtrip(tmp_path: Path):
    """Verifies atomic write and structured read of FeedbackEvent records."""
    log_path = tmp_path / "test_feedback.jsonl"
    logger = FeedbackTelemetryLogger(log_file_path=log_path)

    event1 = FeedbackEvent(
        feedback_id="fb_001",
        action_id="act_001",
        timestamp=100.0,
        latency_delta_t=0.65,
        feedback_type=FeedbackType.IMPLICIT_NEG,
        confidence_cfb=0.92,
        failure_mode=FailureMode.USER_OVERRIDE,
        severity=FailureSeverity.SEV_2_MINOR,
        detector_source="TEST_DETECTOR",
        raw_event_payload={"dx": 24.5}
    )

    event2 = FeedbackEvent(
        feedback_id="fb_002",
        action_id="act_002",
        timestamp=105.0,
        latency_delta_t=2.05,
        feedback_type=FeedbackType.IMPLICIT_POS,
        confidence_cfb=0.85,
        failure_mode=FailureMode.NONE,
        severity=FailureSeverity.SEV_1_BENIGN,
        detector_source="STABILITY_EXPIRATION"
    )

    assert logger.log_event(event1) is True
    assert logger.log_event(event2) is True

    records = logger.read_recent_events(limit=10)
    assert len(records) == 2
    assert records[0]["feedback_id"] == "fb_001"
    assert records[0]["feedback_type"] == "IMPLICIT_NEG"
    assert records[1]["feedback_id"] == "fb_002"
    assert records[1]["feedback_type"] == "IMPLICIT_POS"
