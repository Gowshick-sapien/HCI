"""
Unit tests for GestureVocabulary dictionary loading and metadata lookup.
"""

import pytest
from src.gesture.gesture_vocabulary import GestureVocabulary
from src.storage.schemas import ActionType, GestureToken


def test_gesture_vocabulary_loading():
    vocab = GestureVocabulary()
    assert len(vocab) == 13

    # Check FIST definition
    fist_def = vocab.get_definition(GestureToken.FIST)
    assert fist_def.token == GestureToken.FIST
    assert fist_def.mapped_action == ActionType.NO_ACTION
    assert fist_def.is_rest_state is True
    assert fist_def.requires_gaze_target is False

    # Check PINCH_INDEX definition
    pinch_def = vocab.get_definition(GestureToken.PINCH_INDEX)
    assert pinch_def.token == GestureToken.PINCH_INDEX
    assert pinch_def.mapped_action == ActionType.PRIMARY_CLICK
    assert pinch_def.requires_gaze_target is True

    # Check SWIPE_LEFT definition
    swipe_def = vocab.get_definition(GestureToken.SWIPE_LEFT)
    assert swipe_def.requires_gaze_target is False
    assert swipe_def.mapped_action == ActionType.NAVIGATE_PREVIOUS
