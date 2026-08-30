"""
Master Feedback Observer Subsystem Coordinator (Layer 4).
Orchestrates implicit detection, explicit kinematic classification,
temporal window correlation, and telemetry persistence.
"""

from __future__ import annotations

import logging
import time
from typing import Callable, List, Optional, Tuple

from src.feedback.explicit_classifier import ExplicitFeedbackClassifier
from src.feedback.feedback_correlator import FeedbackCorrelator
from src.feedback.implicit_detector import ImplicitFeedbackDetector
from src.feedback.telemetry_logger import FeedbackTelemetryLogger
from src.storage.schemas import (
    ActionContext,
    FeedbackEvent,
    HeadPoseLandmarks,
    PerceptionFrame,
)

logger = logging.getLogger(__name__)


class FeedbackObserver:
    """
    Unified Layer 4 Supervisory Feedback Coordinator.
    Emits strongly-typed FeedbackEvent records to downstream Layer 5 adaptation engines.
    """

    def __init__(
        self,
        implicit_detector: Optional[ImplicitFeedbackDetector] = None,
        explicit_classifier: Optional[ExplicitFeedbackClassifier] = None,
        correlator: Optional[FeedbackCorrelator] = None,
        telemetry_logger: Optional[FeedbackTelemetryLogger] = None,
    ) -> None:
        self.implicit_detector = implicit_detector or ImplicitFeedbackDetector()
        self.explicit_classifier = explicit_classifier or ExplicitFeedbackClassifier()
        self.correlator = correlator or FeedbackCorrelator()
        self.telemetry_logger = telemetry_logger or FeedbackTelemetryLogger()

        self._listeners: List[Callable[[FeedbackEvent], None]] = []

    def register_feedback_listener(self, listener: Callable[[FeedbackEvent], None]) -> None:
        """Subscribes an asynchronous listener callback to receive emitted FeedbackEvent instances."""
        if listener not in self._listeners:
            self._listeners.append(listener)

    def on_action_executed(self, action: ActionContext) -> None:
        """Notifies the observer that a new multimodal action has been executed."""
        self.correlator.register_action(action)
        logger.debug(f"Registered action {action.action_id} ({action.action_name}) in FeedbackObserver")

    def process_perception_frame(
        self,
        perc_frame: PerceptionFrame,
        timestamp_sec: Optional[float] = None
    ) -> List[FeedbackEvent]:
        """
        Evaluates current perception frame for explicit head gestures and saccadic escape.
        """
        now = timestamp_sec if timestamp_sec is not None else time.time()
        emitted_events: List[FeedbackEvent] = []

        active_action = self.correlator.get_latest_active_action(current_time=now)

        # 1. Evaluate Explicit Head Gestures (Shake / Nod)
        head_event = self.explicit_classifier.update(
            head_pose=perc_frame.head,
            timestamp_sec=now,
            action=active_action
        )
        if head_event:
            validated = self.correlator.process_feedback_event(head_event, current_time=now)
            if validated:
                self._emit_event(validated)
                emitted_events.append(validated)

        # 2. Evaluate Saccadic Gaze Escape if active action has spatial target
        if active_action and active_action.feature_snapshot and active_action.feature_snapshot.gaze_anchor:
            target_xy = active_action.feature_snapshot.gaze_anchor
            saccade_event = self.implicit_detector.evaluate_saccadic_escape(
                action=active_action,
                current_gaze_xy=perc_frame.gaze_screen_xy,
                target_xy=target_xy,
                current_time=now
            )
            if saccade_event:
                validated = self.correlator.process_feedback_event(saccade_event, current_time=now)
                if validated:
                    self._emit_event(validated)
                    emitted_events.append(validated)

        # 3. Check for uncontested actions stability expirations (IMPLICIT_POS)
        expirations = self.correlator.check_stability_expirations(current_time=now)
        for pos_event in expirations:
            self._emit_event(pos_event)
            emitted_events.append(pos_event)

        return emitted_events

    def on_mouse_movement(
        self,
        dx: float,
        dy: float,
        timestamp_sec: Optional[float] = None
    ) -> Optional[FeedbackEvent]:
        """Processes hardware mouse displacement for takeover preemption."""
        now = timestamp_sec if timestamp_sec is not None else time.time()
        active_action = self.correlator.get_latest_active_action(current_time=now)
        if not active_action:
            return None

        event_cand = self.implicit_detector.evaluate_mouse_takeover(
            action=active_action,
            mouse_dx=dx,
            mouse_dy=dy,
            current_time=now
        )
        if event_cand:
            validated = self.correlator.process_feedback_event(event_cand, current_time=now)
            if validated:
                self._emit_event(validated)
                return validated

        return None

    def on_key_event(
        self,
        key_name: str,
        is_ctrl_pressed: bool = False,
        timestamp_sec: Optional[float] = None
    ) -> Optional[FeedbackEvent]:
        """Processes hardware key events for rapid undo / cancellation."""
        now = timestamp_sec if timestamp_sec is not None else time.time()
        active_action = self.correlator.get_latest_active_action(current_time=now)
        if not active_action:
            return None

        event_cand = self.implicit_detector.evaluate_keystroke_undo(
            action=active_action,
            key_name=key_name,
            is_ctrl_pressed=is_ctrl_pressed,
            current_time=now
        )
        if event_cand:
            validated = self.correlator.process_feedback_event(event_cand, current_time=now)
            if validated:
                self._emit_event(validated)
                return validated

        return None

    def _emit_event(self, event: FeedbackEvent) -> None:
        """Logs and dispatches validated FeedbackEvent to all registered listeners."""
        self.telemetry_logger.log_event(event)
        for listener in self._listeners:
            try:
                listener(event)
            except Exception as e:
                logger.error(f"Error in feedback listener callback: {e}")

    def reset(self) -> None:
        """Resets all sub-detectors and action queues."""
        self.explicit_classifier.reset()
        self.implicit_detector.reset()
        self.correlator.reset()


__all__ = ["FeedbackObserver"]

