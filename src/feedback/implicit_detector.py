"""
Implicit User Feedback and Behavioral Conflict Detector.
Observes physical hardware takeovers (mouse displacement, keystroke undos)
and post-action saccadic gaze escapes to infer supervisory feedback signals.
"""

from __future__ import annotations

import math
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from src.storage.schemas import (
    ActionContext,
    FailureMode,
    FailureSeverity,
    FeedbackEvent,
    FeedbackType,
    PerceptionFrame,
)


class ImplicitFeedbackDetector:
    """
    Evaluates real-time hardware telemetry and gaze trajectories
    to detect implicit user corrections and execution confirmations.
    """

    def __init__(
        self,
        mouse_takeover_radius_px: float = 16.0,
        mouse_takeover_window_sec: float = 1.20,
        undo_window_sec: float = 2.00,
        escape_window_sec: float = 1.50,
        saccade_escape_radius_px: float = 150.0,
        saccade_escape_window_sec: float = 0.40,
        stability_expiration_sec: float = 2.00
    ) -> None:
        self.mouse_takeover_radius_px = float(mouse_takeover_radius_px)
        self.mouse_takeover_window_sec = float(mouse_takeover_window_sec)
        self.undo_window_sec = float(undo_window_sec)
        self.escape_window_sec = float(escape_window_sec)
        self.saccade_escape_radius_px = float(saccade_escape_radius_px)
        self.saccade_escape_window_sec = float(saccade_escape_window_sec)
        self.stability_expiration_sec = float(stability_expiration_sec)
        self._action_mouse_disp: Dict[str, float] = {}

    def evaluate_mouse_takeover(
        self,
        action: ActionContext,
        mouse_dx: float,
        mouse_dy: float,
        current_time: Optional[float] = None
    ) -> Optional[FeedbackEvent]:
        """
        Detects physical mouse displacement following an executed multimodal action.
        Supports both single-packet bursts and incremental displacement streams.
        """
        now = current_time if current_time is not None else time.time()
        delta_t = now - action.timestamp_t0

        # Refractory guard (< 0.20s) or expired window (> 1.20s)
        if delta_t < 0.20 or delta_t > self.mouse_takeover_window_sec:
            return None

        current_disp = math.sqrt(mouse_dx ** 2 + mouse_dy ** 2)
        total_disp = self._action_mouse_disp.get(action.action_id, 0.0) + current_disp
        self._action_mouse_disp[action.action_id] = total_disp

        if total_disp >= self.mouse_takeover_radius_px:
            self._action_mouse_disp.pop(action.action_id, None)
            conf = float(max(0.60, min(0.95, 1.0 - (delta_t / self.mouse_takeover_window_sec) * 0.40)))
            return FeedbackEvent(
                feedback_id=f"fb_{uuid.uuid4().hex[:8]}",
                action_id=action.action_id,
                timestamp=now,
                latency_delta_t=delta_t,
                feedback_type=FeedbackType.IMPLICIT_NEG,
                confidence_cfb=conf,
                failure_mode=FailureMode.USER_OVERRIDE,
                severity=FailureSeverity.SEV_2_MINOR,
                detector_source="IMPLICIT_MOUSE_TAKEOVER",
                raw_event_payload={"displacement_px": total_disp, "delta_t": delta_t}
            )

        return None

    def evaluate_keystroke_undo(
        self,
        action: ActionContext,
        key_name: str,
        is_ctrl_pressed: bool = False,
        current_time: Optional[float] = None
    ) -> Optional[FeedbackEvent]:
        """
        Detects keystroke reversals (Ctrl+Z, Escape, Backspace) after action execution.
        """
        now = current_time if current_time is not None else time.time()
        delta_t = now - action.timestamp_t0

        if delta_t < 0.20:
            return None

        # 1. Ctrl+Z (Undo)
        if (key_name.lower() == "z" and is_ctrl_pressed) or key_name == "Key.undo":
            if delta_t <= self.undo_window_sec:
                return FeedbackEvent(
                    feedback_id=f"fb_{uuid.uuid4().hex[:8]}",
                    action_id=action.action_id,
                    timestamp=now,
                    latency_delta_t=delta_t,
                    feedback_type=FeedbackType.IMPLICIT_NEG,
                    confidence_cfb=0.95,
                    failure_mode=FailureMode.FALSE_ACTIVATION,
                    severity=FailureSeverity.SEV_3_MODERATE,
                    detector_source="IMPLICIT_CTRL_Z_UNDO",
                    raw_event_payload={"key": "Ctrl+Z", "delta_t": delta_t}
                )

        # 2. Escape (Abort / Cancel)
        if key_name.lower() in ("esc", "escape", "key.esc"):
            if delta_t <= self.escape_window_sec:
                return FeedbackEvent(
                    feedback_id=f"fb_{uuid.uuid4().hex[:8]}",
                    action_id=action.action_id,
                    timestamp=now,
                    latency_delta_t=delta_t,
                    feedback_type=FeedbackType.IMPLICIT_NEG,
                    confidence_cfb=0.85,
                    failure_mode=FailureMode.WRONG_TARGET,
                    severity=FailureSeverity.SEV_2_MINOR,
                    detector_source="IMPLICIT_ESCAPE_CANCEL",
                    raw_event_payload={"key": "Escape", "delta_t": delta_t}
                )

        # 3. Backspace (Immediate Edit Reversal)
        if key_name.lower() in ("backspace", "key.backspace"):
            if delta_t <= 1.20:
                return FeedbackEvent(
                    feedback_id=f"fb_{uuid.uuid4().hex[:8]}",
                    action_id=action.action_id,
                    timestamp=now,
                    latency_delta_t=delta_t,
                    feedback_type=FeedbackType.IMPLICIT_NEG,
                    confidence_cfb=0.80,
                    failure_mode=FailureMode.FALSE_ACTIVATION,
                    severity=FailureSeverity.SEV_2_MINOR,
                    detector_source="IMPLICIT_BACKSPACE_REVERSAL",
                    raw_event_payload={"key": "Backspace", "delta_t": delta_t}
                )

        return None

    def evaluate_saccadic_escape(
        self,
        action: ActionContext,
        current_gaze_xy: Tuple[float, float],
        target_xy: Optional[Tuple[float, float]],
        current_time: Optional[float] = None
    ) -> Optional[FeedbackEvent]:
        """
        Detects sudden saccadic gaze escape away from the intended action target.
        """
        if target_xy is None:
            return None

        now = current_time if current_time is not None else time.time()
        delta_t = now - action.timestamp_t0

        if delta_t < 0.15 or delta_t > self.saccade_escape_window_sec:
            return None

        dist = math.sqrt((current_gaze_xy[0] - target_xy[0]) ** 2 + (current_gaze_xy[1] - target_xy[1]) ** 2)
        if dist >= self.saccade_escape_radius_px:
            return FeedbackEvent(
                feedback_id=f"fb_{uuid.uuid4().hex[:8]}",
                action_id=action.action_id,
                timestamp=now,
                latency_delta_t=delta_t,
                feedback_type=FeedbackType.IMPLICIT_NEG,
                confidence_cfb=0.70,
                failure_mode=FailureMode.WRONG_TARGET,
                severity=FailureSeverity.SEV_2_MINOR,
                detector_source="IMPLICIT_SACCADIC_ESCAPE",
                raw_event_payload={"gaze_escape_distance_px": dist, "delta_t": delta_t}
            )

        return None

    def evaluate_stability_expiration(
        self,
        action: ActionContext,
        current_time: Optional[float] = None
    ) -> Optional[FeedbackEvent]:
        """
        Generates positive implicit feedback when an action remains uncontested past stability timeout.
        """
        now = current_time if current_time is not None else time.time()
        delta_t = now - action.timestamp_t0

        if delta_t >= self.stability_expiration_sec:
            return FeedbackEvent(
                feedback_id=f"fb_{uuid.uuid4().hex[:8]}",
                action_id=action.action_id,
                timestamp=now,
                latency_delta_t=delta_t,
                feedback_type=FeedbackType.IMPLICIT_POS,
                confidence_cfb=0.80,
                failure_mode=FailureMode.NONE,
                severity=FailureSeverity.SEV_1_BENIGN,
                detector_source="IMPLICIT_STABILITY_EXPIRATION",
                raw_event_payload={"stability_duration_sec": delta_t}
            )

        return None

    def reset(self) -> None:
        """Resets all internal displacement and tracking buffers."""
        self._action_mouse_disp.clear()


__all__ = ["ImplicitFeedbackDetector"]

