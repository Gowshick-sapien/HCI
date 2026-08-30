"""
Unit tests for Layer 4 Explicit Head Gesture Classifier.
Verifies Invariant INV-D4.3: Head shake (yaw oscillation) and head nod (pitch oscillation).
"""

import numpy as np
import pytest

from src.feedback.explicit_classifier import ExplicitFeedbackClassifier
from src.storage.schemas import (
    FailureMode,
    FeedbackType,
    HeadPoseLandmarks,
)


def _mock_head_pose(yaw: float, pitch: float, roll: float = 0.0) -> HeadPoseLandmarks:
    return HeadPoseLandmarks(
        yaw=yaw,
        pitch=pitch,
        roll=roll,
        translation_vector=(0.0, 0.0, 500.0),
        mahalanobis_distance=0.0,
        confidence=1.0
    )


def test_head_shake_rejection_invariant():
    """Invariant INV-D4.3: Head yaw oscillation >= +-12 deg (1.5-3.0 Hz) triggers EXPLICIT_NEG."""
    classifier = ExplicitFeedbackClassifier(min_yaw_amplitude_deg=20.0, min_zero_crossings=3)

    # Generate synthetic head shake (yaw oscillating +/- 15 degrees at 2.0 Hz over 1.0s, 30 fps)
    t = np.linspace(0.0, 1.0, 30)
    yaw_osc = 15.0 * np.sin(2.0 * np.pi * 2.0 * t)

    detected_event = None
    for i, now in enumerate(t):
        hp = _mock_head_pose(yaw=float(yaw_osc[i]), pitch=0.0)
        ev = classifier.update(hp, timestamp_sec=now)
        if ev:
            detected_event = ev

    assert detected_event is not None
    assert detected_event.feedback_type == FeedbackType.IMPLICIT_NEG
    assert detected_event.failure_mode == FailureMode.USER_OVERRIDE
    assert detected_event.confidence_cfb >= 0.85
    assert detected_event.detector_source == "EXPLICIT_HEAD_SHAKE"


def test_head_nod_confirmation():
    """Head pitch oscillation >= +-8 deg triggers EXPLICIT_POS."""
    classifier = ExplicitFeedbackClassifier(min_pitch_amplitude_deg=14.0, min_zero_crossings=3)

    # Generate synthetic head nod (pitch oscillating +/- 10 degrees at 2.0 Hz)
    t = np.linspace(0.0, 1.0, 30)
    pitch_osc = 10.0 * np.sin(2.0 * np.pi * 2.0 * t)

    detected_event = None
    for i, now in enumerate(t):
        hp = _mock_head_pose(yaw=0.0, pitch=float(pitch_osc[i]))
        ev = classifier.update(hp, timestamp_sec=now)
        if ev:
            detected_event = ev

    assert detected_event is not None
    assert detected_event.feedback_type == FeedbackType.IMPLICIT_POS
    assert detected_event.detector_source == "EXPLICIT_HEAD_NOD"


def test_still_posture_no_false_positive():
    """Static or gently shifting head posture must not trigger gestures."""
    classifier = ExplicitFeedbackClassifier()

    t = np.linspace(0.0, 1.0, 30)
    for now in t:
        # Constant slight tilt
        hp = _mock_head_pose(yaw=3.0, pitch=-5.0)
        ev = classifier.update(hp, timestamp_sec=now)
        assert ev is None
