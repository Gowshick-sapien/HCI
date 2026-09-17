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


def test_gesture_classifier_swipe_vertical():
    """Verify SWIPE_UP and SWIPE_DOWN detection with dynamic high-velocity vertical translation."""
    classifier = GestureClassifier()

    # Initial frame: Open hand at y=0.6
    raw_lms1 = [(0.5, 0.6, 0.0)] * 21
    raw_lms1[0] = (0.5, 0.6, 0.0)
    raw_lms1[4] = (0.35, 0.5, 0.0)
    raw_lms1[8] = (0.45, 0.3, 0.0)
    raw_lms1[12] = (0.50, 0.3, 0.0)
    raw_lms1[16] = (0.55, 0.3, 0.0)
    raw_lms1[20] = (0.60, 0.35, 0.0)

    hand1 = HandLandmarks(
        is_detected=True, pinch_distance=0.2, palm_normal=(0.0, 0.0, 1.0),
        wrist_position=(0.5, 0.6, 0.0), wrist_velocity=0.0,
        gesture_class="HAND_DETECTED", confidence=0.9, variance=0.01,
        raw_landmarks_21=raw_lms1
    )
    res1 = classifier.classify(hand1, timestamp_ms=0.0)
    assert res1.gesture_token == GestureToken.OPEN_PALM

    # Second frame: Upward translation to y=0.4 with high velocity (SWIPE_UP)
    raw_lms2 = [(0.5, 0.4, 0.0)] * 21
    raw_lms2[0] = (0.5, 0.4, 0.0)
    raw_lms2[4] = (0.35, 0.3, 0.0)
    raw_lms2[8] = (0.45, 0.1, 0.0)
    raw_lms2[12] = (0.50, 0.1, 0.0)
    raw_lms2[16] = (0.55, 0.1, 0.0)
    raw_lms2[20] = (0.60, 0.15, 0.0)

    hand2 = HandLandmarks(
        is_detected=True, pinch_distance=0.2, palm_normal=(0.0, 0.0, 1.0),
        wrist_position=(0.5, 0.4, 0.0), wrist_velocity=3.0,
        gesture_class="HAND_DETECTED", confidence=0.9, variance=0.01,
        raw_landmarks_21=raw_lms2
    )
    res2 = classifier.classify(hand2, timestamp_ms=33.3)
    assert res2.gesture_token == GestureToken.SWIPE_UP
    assert res2.action_intent == "SCROLL_UP"
    assert res2.requires_gaze_target is False

    # Third frame: Downward translation to y=0.65 with high velocity (SWIPE_DOWN)
    raw_lms3 = [(0.5, 0.65, 0.0)] * 21
    raw_lms3[0] = (0.5, 0.65, 0.0)
    raw_lms3[4] = (0.35, 0.55, 0.0)
    raw_lms3[8] = (0.45, 0.35, 0.0)
    raw_lms3[12] = (0.50, 0.35, 0.0)
    raw_lms3[16] = (0.55, 0.35, 0.0)
    raw_lms3[20] = (0.60, 0.40, 0.0)

    hand3 = HandLandmarks(
        is_detected=True, pinch_distance=0.2, palm_normal=(0.0, 0.0, 1.0),
        wrist_position=(0.5, 0.65, 0.0), wrist_velocity=3.0,
        gesture_class="HAND_DETECTED", confidence=0.9, variance=0.01,
        raw_landmarks_21=raw_lms3
    )
    res3 = classifier.classify(hand3, timestamp_ms=66.6)
    assert res3.gesture_token == GestureToken.SWIPE_DOWN
    assert res3.action_intent == "SCROLL_DOWN"
    assert res3.requires_gaze_target is False


def test_gesture_classifier_thumbs_up():
    """Verify THUMBS_UP detection when 4 fingers are curled and thumb points upward."""
    classifier = GestureClassifier()

    raw_lms = [(0.5, 0.5, 0.0)] * 21
    raw_lms[0] = (0.5, 0.7, 0.0)
    raw_lms[9] = (0.5, 0.52, 0.0)

    for mcp, tip in [(5, 8), (9, 12), (13, 16), (17, 20)]:
        raw_lms[mcp] = (0.45, 0.52, 0.0)
        raw_lms[mcp+1] = (0.45, 0.47, 0.0)
        raw_lms[mcp+2] = (0.45, 0.57, 0.0)
        raw_lms[tip] = (0.45, 0.60, 0.0)

    raw_lms[2] = (0.40, 0.55, 0.0)
    raw_lms[3] = (0.40, 0.47, 0.0)
    raw_lms[4] = (0.40, 0.42, 0.0)

    hand = HandLandmarks(
        is_detected=True, pinch_distance=0.2, palm_normal=(0, 0, 1),
        wrist_position=(0.5, 0.7, 0.0), wrist_velocity=0.0,
        gesture_class="HAND_DETECTED", confidence=0.9, variance=0.01,
        raw_landmarks_21=raw_lms
    )

    res = classifier.classify(hand, timestamp_ms=0.0)
    assert res.gesture_token == GestureToken.THUMBS_UP
    assert res.action_intent == "CONFIRM_SUBMIT"
    assert res.requires_gaze_target is False
    assert res.c_gesture >= 0.75


def test_gesture_classifier_swipe_horizontal():
    """Verify SWIPE_LEFT and SWIPE_RIGHT detection with camera mirror mapping."""
    classifier = GestureClassifier()

    # Initial frame at x=0.5
    raw_lms1 = [(0.5, 0.5, 0.0)] * 21
    raw_lms1[0] = (0.5, 0.5, 0.0)
    hand1 = HandLandmarks(
        is_detected=True, pinch_distance=0.2, palm_normal=(0.0, 0.0, 1.0),
        wrist_position=(0.5, 0.5, 0.0), wrist_velocity=0.0,
        gesture_class="HAND_DETECTED", confidence=0.9, variance=0.01,
        raw_landmarks_21=raw_lms1
    )
    classifier.classify(hand1, timestamp_ms=0.0)

    # Frame 2: Hand moves to camera left (dx < 0 -> SWIPE_RIGHT in mirror view)
    raw_lms2 = [(0.35, 0.5, 0.0)] * 21
    raw_lms2[0] = (0.35, 0.5, 0.0)
    hand2 = HandLandmarks(
        is_detected=True, pinch_distance=0.2, palm_normal=(0.0, 0.0, 1.0),
        wrist_position=(0.35, 0.5, 0.0), wrist_velocity=2.0,
        gesture_class="HAND_DETECTED", confidence=0.9, variance=0.01,
        raw_landmarks_21=raw_lms2
    )
    res2 = classifier.classify(hand2, timestamp_ms=33.3)
    assert res2.gesture_token == GestureToken.SWIPE_RIGHT
    assert res2.action_intent == "NAVIGATE_NEXT"

    # Frame 3: Hand moves to camera right (dx > 0 -> SWIPE_LEFT in mirror view)
    raw_lms3 = [(0.65, 0.5, 0.0)] * 21
    raw_lms3[0] = (0.65, 0.5, 0.0)
    hand3 = HandLandmarks(
        is_detected=True, pinch_distance=0.2, palm_normal=(0.0, 0.0, 1.0),
        wrist_position=(0.65, 0.5, 0.0), wrist_velocity=2.0,
        gesture_class="HAND_DETECTED", confidence=0.9, variance=0.01,
        raw_landmarks_21=raw_lms3
    )
    res3 = classifier.classify(hand3, timestamp_ms=66.6)
    assert res3.gesture_token == GestureToken.SWIPE_LEFT
    assert res3.action_intent == "NAVIGATE_PREVIOUS"


