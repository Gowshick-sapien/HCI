"""
Temporal Feedback Correlator and Failure Taxonomy Mapper.
Associates asynchronous implicit/explicit feedback events with corresponding executed ActionContext
records across the 3-stage temporal evaluation window.
"""

from __future__ import annotations

import collections
import logging
import threading
import time
from typing import Deque, Dict, List, Optional

from src.storage.schemas import (
    ActionContext,
    FailureMode,
    FailureSeverity,
    FeedbackEvent,
    FeedbackType,
    FeedbackWindow,
)

logger = logging.getLogger(__name__)


class FeedbackCorrelator:
    """
    Thread-safe temporal correlation coordinator for Layer 4.
    Tracks executed actions and resolves supervisory feedback events.
    """

    def __init__(
        self,
        refractory_period_sec: float = 0.20,
        correction_window_sec: float = 2.00,
        expiration_timeout_sec: float = 2.50,
        max_action_history: int = 30
    ) -> None:
        self.refractory_period_sec = float(refractory_period_sec)
        self.correction_window_sec = float(correction_window_sec)
        self.expiration_timeout_sec = float(expiration_timeout_sec)
        self.max_action_history = int(max_action_history)

        # Thread-safe ring buffer of active/recent actions: action_id -> ActionContext
        self._lock = threading.RLock()
        self._active_actions: Dict[str, ActionContext] = {}
        self._action_queue: Deque[str] = collections.deque()
        self._resolved_actions: set[str] = set()

    def register_action(self, action: ActionContext) -> None:
        """
        Registers an executed action context into the correlation monitor buffer.
        """
        with self._lock:
            self._active_actions[action.action_id] = action
            self._action_queue.append(action.action_id)

            # Purge oldest actions if buffer capacity exceeded
            while len(self._action_queue) > self.max_action_history:
                old_id = self._action_queue.popleft()
                self._active_actions.pop(old_id, None)
                self._resolved_actions.discard(old_id)

    def _get_latest_active_action_unlocked(self, current_time: float) -> Optional[ActionContext]:
        for action_id in reversed(self._action_queue):
            action = self._active_actions.get(action_id)
            if action and action_id not in self._resolved_actions:
                delta_t = current_time - action.timestamp_t0
                if delta_t <= self.expiration_timeout_sec:
                    return action
        return None

    def get_latest_active_action(self, current_time: Optional[float] = None) -> Optional[ActionContext]:
        """
        Retrieves the most recent executed action within the active evaluation window.
        """
        now = current_time if current_time is not None else time.time()
        with self._lock:
            return self._get_latest_active_action_unlocked(now)

    def process_feedback_event(
        self,
        feedback: FeedbackEvent,
        current_time: Optional[float] = None
    ) -> Optional[FeedbackEvent]:
        """
        Validates and correlates a feedback event against temporal window invariants.

        Returns:
            Correlated FeedbackEvent if accepted, None if suppressed (e.g. within refractory period).
        """
        now = current_time if current_time is not None else time.time()

        with self._lock:
            action = self._active_actions.get(feedback.action_id)
            if not action:
                # If specific action not found, attempt to correlate with latest active action
                action = self._get_latest_active_action_unlocked(current_time=now)
                if not action:
                    return feedback # Retain general unassociated feedback

            delta_t = now - action.timestamp_t0

            # Invariant INV-D4.4: Refractory period suppression
            if delta_t < self.refractory_period_sec:
                logger.debug(f"Suppressed feedback {feedback.feedback_id}: delta_t={delta_t:.3f}s < refractory {self.refractory_period_sec}s")
                return None

            # Mark action as resolved so subsequent duplicate events are ignored
            self._resolved_actions.add(action.action_id)

            # Re-bind feedback to confirmed action
            return FeedbackEvent(
                feedback_id=feedback.feedback_id,
                action_id=action.action_id,
                timestamp=now,
                latency_delta_t=delta_t,
                feedback_type=feedback.feedback_type,
                confidence_cfb=feedback.confidence_cfb,
                failure_mode=feedback.failure_mode,
                severity=feedback.severity,
                detector_source=feedback.detector_source,
                raw_event_payload=feedback.raw_event_payload
            )

    def check_stability_expirations(self, current_time: Optional[float] = None) -> List[FeedbackEvent]:
        """
        Checks for uncontested actions past the stability timeout and emits IMPLICIT_POS events.
        """
        now = current_time if current_time is not None else time.time()
        positive_events: List[FeedbackEvent] = []

        with self._lock:
            for action_id in list(self._action_queue):
                if action_id not in self._resolved_actions:
                    action = self._active_actions.get(action_id)
                    if action:
                        delta_t = now - action.timestamp_t0
                        if delta_t >= self.correction_window_sec:
                            self._resolved_actions.add(action_id)
                            pos_event = FeedbackEvent(
                                feedback_id=f"pos_{action_id[-8:]}",
                                action_id=action_id,
                                timestamp=now,
                                latency_delta_t=delta_t,
                                feedback_type=FeedbackType.IMPLICIT_POS,
                                confidence_cfb=0.85,
                                failure_mode=FailureMode.NONE,
                                severity=FailureSeverity.SEV_1_BENIGN,
                                detector_source="STABILITY_EXPIRATION_MONITOR",
                                raw_event_payload={"stability_sec": delta_t}
                            )
                            positive_events.append(pos_event)

        return positive_events

    def reset(self) -> None:
        """Clears all tracking queues and active history."""
        with self._lock:
            self._active_actions.clear()
            self._action_queue.clear()
            self._resolved_actions.clear()


__all__ = ["FeedbackCorrelator"]
