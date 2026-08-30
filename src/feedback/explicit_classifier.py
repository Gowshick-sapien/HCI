"""
Explicit Head Gesture and Discard Feedback Classifier.
Analyzes oscillatory head kinematics (head shakes, head nods) to infer
explicit supervisory confirmation or rejection signals.
"""

from __future__ import annotations

import collections
import time
import uuid
from typing import Deque, Optional, Tuple

import numpy as np

from src.storage.schemas import (
    ActionContext,
    FailureMode,
    FailureSeverity,
    FeedbackEvent,
    FeedbackType,
    HeadPoseLandmarks,
)


class ExplicitFeedbackClassifier:
    """
    Kinematic zero-crossing classifier for head gestures.
    Detects sinusoidal head shakes (rejection) and head nods (confirmation).
    """

    def __init__(
        self,
        window_duration_sec: float = 1.20,
        min_yaw_amplitude_deg: float = 20.0,
        min_pitch_amplitude_deg: float = 14.0,
        min_zero_crossings: int = 3,
        cooldown_duration_sec: float = 1.50
    ) -> None:
        self.window_duration_sec = float(window_duration_sec)
        self.min_yaw_amplitude_deg = float(min_yaw_amplitude_deg)
        self.min_pitch_amplitude_deg = float(min_pitch_amplitude_deg)
        self.min_zero_crossings = int(min_zero_crossings)
        self.cooldown_duration_sec = float(cooldown_duration_sec)

        # Rolling history buffer: [(timestamp, yaw, pitch, roll)]
        self._history: Deque[Tuple[float, float, float, float]] = collections.deque()
        self._last_trigger_timestamp: float = -999.0

    def update(
        self,
        head_pose: HeadPoseLandmarks,
        timestamp_sec: Optional[float] = None,
        action: Optional[ActionContext] = None
    ) -> Optional[FeedbackEvent]:
        """
        Updates kinematic buffer with current head Euler angles and evaluates gesture oscillations.

        Args:
            head_pose: Current HeadPoseLandmarks instance.
            timestamp_sec: Current timestamp in seconds.
            action: Optional recent ActionContext to correlate with.

        Returns:
            FeedbackEvent if a head shake/nod is recognized, None otherwise.
        """
        now = timestamp_sec if timestamp_sec is not None else time.time()

        # Append sample
        self._history.append((now, head_pose.yaw, head_pose.pitch, head_pose.roll))

        # Purge stale samples outside window
        while self._history and (now - self._history[0][0]) > self.window_duration_sec:
            self._history.popleft()

        # Cooldown guard to prevent repeated firing for the same gesture
        if (now - self._last_trigger_timestamp) < self.cooldown_duration_sec:
            return None

        if len(self._history) < 15:
            return None

        # Extract yaw and pitch arrays
        timestamps = np.array([item[0] for item in self._history])
        yaws = np.array([item[1] for item in self._history])
        pitches = np.array([item[2] for item in self._history])

        # 1. Evaluate Head Shake (Horizontal Yaw Oscillation)
        shake_detected, shake_conf = self._detect_oscillation(
            yaws, self.min_yaw_amplitude_deg, self.min_zero_crossings
        )
        if shake_detected:
            self._last_trigger_timestamp = now
            delta_t = now - action.timestamp_t0 if action else 0.50
            return FeedbackEvent(
                feedback_id=f"fb_{uuid.uuid4().hex[:8]}",
                action_id=action.action_id if action else "general_rejection",
                timestamp=now,
                latency_delta_t=delta_t,
                feedback_type=FeedbackType.IMPLICIT_NEG,
                confidence_cfb=shake_conf,
                failure_mode=FailureMode.USER_OVERRIDE,
                severity=FailureSeverity.SEV_3_MODERATE,
                detector_source="EXPLICIT_HEAD_SHAKE",
                raw_event_payload={"gesture": "HEAD_SHAKE", "peak_to_peak_yaw": float(np.ptp(yaws))}
            )

        # 2. Evaluate Head Nod (Vertical Pitch Oscillation)
        nod_detected, nod_conf = self._detect_oscillation(
            pitches, self.min_pitch_amplitude_deg, self.min_zero_crossings
        )
        if nod_detected:
            self._last_trigger_timestamp = now
            delta_t = now - action.timestamp_t0 if action else 0.50
            return FeedbackEvent(
                feedback_id=f"fb_{uuid.uuid4().hex[:8]}",
                action_id=action.action_id if action else "general_confirm",
                timestamp=now,
                latency_delta_t=delta_t,
                feedback_type=FeedbackType.IMPLICIT_POS,
                confidence_cfb=nod_conf,
                failure_mode=FailureMode.NONE,
                severity=FailureSeverity.SEV_1_BENIGN,
                detector_source="EXPLICIT_HEAD_NOD",
                raw_event_payload={"gesture": "HEAD_NOD", "peak_to_peak_pitch": float(np.ptp(pitches))}
            )

        return None

    @staticmethod
    def _detect_oscillation(
        values: np.ndarray,
        min_amplitude: float,
        min_zero_crossings: int
    ) -> Tuple[bool, float]:
        """Detects zero-crossing sinusoidal oscillation around mean value."""
        ptp = float(np.ptp(values))
        if ptp < min_amplitude:
            return False, 0.0

        # Mean-centered series
        centered = values - np.mean(values)

        # Count zero-crossings (sign changes)
        signs = np.sign(centered)
        # Replace exact zeros with previous sign
        for i in range(1, len(signs)):
            if signs[i] == 0:
                signs[i] = signs[i - 1]

        zero_crossings = int(np.sum(np.diff(signs) != 0))

        if zero_crossings >= min_zero_crossings:
            # Confidence scales with amplitude and regularity
            conf = float(min(0.98, max(0.75, 0.70 + (ptp / (min_amplitude * 2.0)) * 0.25)))
            return True, conf

        return False, 0.0

    def reset(self) -> None:
        """Clears kinematic rolling history."""
        self._history.clear()
        self._last_trigger_timestamp = -999.0


__all__ = ["ExplicitFeedbackClassifier"]
