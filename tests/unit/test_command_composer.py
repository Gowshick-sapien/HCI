"""
Unit tests for Stage 3A Multimodal Command Composer.
Verifies Invariants INV-D2.3 and INV-D2.4: Spatial-Intent Binding & Midas Touch Suppression.
"""

import pytest

from src.fusion.command_composer import CommandComposer
from src.storage.schemas import (
    ActionType,
    EyeLandmarks,
    GestureClassification,
    GestureToken,
    HandLandmarks,
    HeadPoseLandmarks,
    PerceptionFrame,
)


def _create_mock_perception_frame(gaze_anchor=None, gaze_dwell_ms=0.0):
    eye = EyeLandmarks(
        left_iris_center=(300.0, 400.0), right_iris_center=(370.0, 400.0),
        left_ear=0.28, right_ear=0.28, iris_ratio_x=0.5, iris_ratio_y=0.5,
        confidence=0.90
    )
    head = HeadPoseLandmarks(
        yaw=0.0, pitch=0.0, roll=0.0, translation_vector=(0.0, 0.0, 0.0),
        mahalanobis_distance=0.5, confidence=0.95
    )
    hand = HandLandmarks(
        is_detected=True, pinch_distance=0.02, palm_normal=(0, 0, 1),
        wrist_position=(0.5, 0.5, 0), wrist_velocity=0.1, gesture_class="PINCH",
        confidence=0.90
    )
    return PerceptionFrame(
        frame_id=1, timestamp_ms=1000.0, eye=eye, head=head, hand=hand,
        gaze_confidence=0.90, head_confidence=0.95, gaze_screen_xy=(960.0, 540.0),
        head_euler_angles=(0.0, 0.0, 0.0), gaze_dwell_ms=gaze_dwell_ms,
        gaze_stability=1.0, gaze_anchor=gaze_anchor
    )


def test_command_composer_spatial_binding_invariant():
    """Invariant INV-D2.3: Spatial gestures require locked gaze_anchor."""
    composer = CommandComposer()

    gesture_pinch = GestureClassification(
        gesture_token=GestureToken.PINCH_INDEX,
        c_gesture=0.88,
        requires_gaze_target=True,
        action_intent="PRIMARY_CLICK",
        stable_duration_ms=100.0,
        timestamp_ms=1000.0
    )

    # 1. Unanchored Gaze -> Midas Touch suppression (ActionType.NO_ACTION)
    perc_unanchored = _create_mock_perception_frame(gaze_anchor=None, gaze_dwell_ms=40.0)
    cmd_unbound = composer.compose(perc_unanchored, gesture_pinch)
    assert cmd_unbound.action_type == ActionType.NO_ACTION
    assert cmd_unbound.gaze_anchor is None
    assert cmd_unbound.requires_gaze_target is True

    # 2. Anchored Gaze -> Dispatches PRIMARY_CLICK to anchor coordinates
    perc_anchored = _create_mock_perception_frame(gaze_anchor=(800.0, 450.0), gaze_dwell_ms=150.0)
    cmd_bound = composer.compose(perc_anchored, gesture_pinch)
    assert cmd_bound.action_type == ActionType.PRIMARY_CLICK
    assert cmd_bound.gaze_anchor == (800.0, 450.0)
    assert cmd_bound.composed_score > 0.70


def test_command_composer_global_non_spatial_gestures():
    """Invariant INV-D2.4: Global gestures emit commands without gaze requirement."""
    composer = CommandComposer()

    gesture_swipe = GestureClassification(
        gesture_token=GestureToken.SWIPE_LEFT,
        c_gesture=0.85,
        requires_gaze_target=False,
        action_intent="NAVIGATE_PREVIOUS",
        stable_duration_ms=50.0,
        timestamp_ms=1000.0
    )

    perc_no_anchor = _create_mock_perception_frame(gaze_anchor=None)
    cmd_swipe = composer.compose(perc_no_anchor, gesture_swipe)
    assert cmd_swipe.action_type == ActionType.NAVIGATE_PREVIOUS
    assert cmd_swipe.gaze_anchor is None
    assert cmd_swipe.requires_gaze_target is False
