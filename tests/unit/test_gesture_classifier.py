"""
Unit tests for GestureClassifier and FIST REST Guard.
"""

import numpy as np
import pytest

from src.gesture.gesture_classifier import GestureClassifier
from src.storage.schemas import GestureToken, HandLandmarks


def test_gesture_classifier_fist_guard_invariant():
    """Invariant INV-D1.5: FIST gesture token always emits action_intent = NO_ACTION."""
    classifier = GestureClassifier()

    # Generate 50 synthetic curled-finger landmark traces
    np.random.seed(42)
    for trial_id in range(50):
        # Create curled landmarks where all fingertips are close to palm/MCPs
        raw_lms = []
        for i in range(21):
            if i in [4, 8, 12, 16, 20]:
                # Curled tips close to palm origin (0.5, 0.5)
                raw_lms.append((0.50 + np.random.uniform(-0.02, 0.02), 0.50 + np.random.uniform(-0.02, 0.02), 0.0))
            elif i in [2, 6, 10, 14, 18]:
                # PIP/MCPs slightly extended outward
                raw_lms.append((0.50 + np.random.uniform(-0.08, 0.08), 0.50 + np.random.uniform(0.05, 0.10), 0.0))
            else:
                raw_lms.append((0.50, 0.50, 0.0))

        hand = HandLandmarks(
            is_detected=True,
            pinch_distance=0.10,
            palm_normal=(0.0, 0.0, 1.0),
            wrist_position=(0.5, 0.5, 0.0),
            wrist_velocity=0.1,
            gesture_class="HAND_DETECTED",
            confidence=0.90,
            variance=0.04,
            raw_landmarks_21=raw_lms
        )

        result = classifier.classify(hand, timestamp_ms=float(trial_id * 33.3))
        assert result.gesture_token == GestureToken.FIST
        assert result.action_intent == "NO_ACTION"
        assert result.requires_gaze_target is False
        assert result.c_gesture > 0.50


def test_gesture_classifier_pinch_index():
    classifier = GestureClassifier(default_pinch_threshold=0.065)

    # Synthetic hand with index tip touching thumb tip
    raw_lms = [(0.5, 0.5, 0.0)] * 21
    raw_lms[4] = (0.45, 0.45, 0.0) # thumb tip
    raw_lms[8] = (0.46, 0.45, 0.0) # index tip (gap = 0.01 < 0.065)
    # Extend other fingers to prevent FIST
    raw_lms[12] = (0.45, 0.80, 0.0) # middle tip
    raw_lms[16] = (0.45, 0.80, 0.0) # ring tip
    raw_lms[20] = (0.45, 0.80, 0.0) # pinky tip

    hand = HandLandmarks(
        is_detected=True,
        pinch_distance=0.01,
        palm_normal=(0.0, 0.0, 1.0),
        wrist_position=(0.5, 0.5, 0.0),
        wrist_velocity=0.2,
        gesture_class="HAND_DETECTED",
        confidence=0.90,
        variance=0.04,
        raw_landmarks_21=raw_lms
    )

    result = classifier.classify(hand, timestamp_ms=100.0)
    assert result.gesture_token == GestureToken.PINCH_INDEX
    assert result.action_intent == "PRIMARY_CLICK"
    assert result.requires_gaze_target is True
    assert result.c_gesture >= 0.70
