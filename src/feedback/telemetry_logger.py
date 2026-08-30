"""
Feedback Telemetry Logger.
Handles non-blocking, thread-safe persistence of structured FeedbackEvent records
to logs/feedback_events.jsonl for runtime assessment and offline analysis.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.storage.schemas import (
    FailureMode,
    FailureSeverity,
    FeedbackEvent,
    FeedbackType,
)

logger = logging.getLogger(__name__)


class FeedbackTelemetryLogger:
    """
    JSONL logger for supervisory feedback telemetry.
    Thread-safe append operations with automatic file rotation.
    """

    DEFAULT_LOG_PATH = Path(__file__).resolve().parent.parent.parent / "logs" / "feedback_events.jsonl"

    def __init__(
        self,
        log_file_path: Optional[Path] = None,
        max_file_size_mb: float = 25.0
    ) -> None:
        self.log_file_path = Path(log_file_path) if log_file_path else self.DEFAULT_LOG_PATH
        self.max_file_size_bytes = int(max_file_size_mb * 1024 * 1024)
        self._lock = threading.RLock()

        # Ensure directory exists
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(self, event: FeedbackEvent) -> bool:
        """
        Appends a FeedbackEvent to the JSONL log file.

        Args:
            event: Strongly-typed FeedbackEvent instance.

        Returns:
            True if log write succeeded, False otherwise.
        """
        payload = self._serialize_event(event)

        with self._lock:
            try:
                self._check_rotation()
                with open(self.log_file_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(payload) + "\n")
                return True
            except Exception as e:
                logger.error(f"Failed to log feedback event {event.feedback_id}: {e}")
                return False

    def read_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Reads the most recent N feedback events from the log file.
        """
        if not self.log_file_path.exists():
            return []

        with self._lock:
            try:
                with open(self.log_file_path, "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f if line.strip()]

                recent_lines = lines[-limit:] if len(lines) > limit else lines
                return [json.loads(line) for line in recent_lines]
            except Exception as e:
                logger.error(f"Error reading feedback log: {e}")
                return []

    def _check_rotation(self) -> None:
        """Rotates the log file if it exceeds maximum size."""
        if self.log_file_path.exists():
            try:
                if self.log_file_path.stat().st_size >= self.max_file_size_bytes:
                    backup = self.log_file_path.with_suffix(".jsonl.old")
                    if backup.exists():
                        backup.unlink()
                    self.log_file_path.rename(backup)
                    logger.info(f"Rotated feedback log to {backup}")
            except Exception as e:
                logger.warning(f"Log rotation check failed: {e}")

    @staticmethod
    def _serialize_event(event: FeedbackEvent) -> Dict[str, Any]:
        """Serializes FeedbackEvent into a JSON-compatible dictionary."""
        return {
            "feedback_id": event.feedback_id,
            "action_id": event.action_id,
            "timestamp": float(event.timestamp),
            "latency_delta_t": float(event.latency_delta_t),
            "feedback_type": event.feedback_type.value,
            "confidence_cfb": float(event.confidence_cfb),
            "failure_mode": event.failure_mode.value,
            "severity": int(event.severity.value if hasattr(event.severity, "value") else event.severity),
            "detector_source": str(event.detector_source),
            "raw_event_payload": event.raw_event_payload
        }


__all__ = ["FeedbackTelemetryLogger"]
