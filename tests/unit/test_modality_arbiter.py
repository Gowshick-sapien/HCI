"""
Unit tests for ModalityArbiter priority arbitration logic.
"""

import time
import pytest

from src.gesture.modality_arbiter import ModalityArbiter
from src.storage.schemas import DeviceMode, GestureClassification, GestureToken


def test_modality_arbiter_priority_modes():
    """Invariant INV-D1.6: Emits correct DeviceMode across all 4 operational states."""
    arbiter = ModalityArbiter(
        keyboard_timeout_ms=1500.0,
        mouse_timeout_ms=800.0,
        soft_reduction_factor=0.50,
        enable_pynput_hooks=False # Use synthetic events for deterministic unit tests
    )

    t0 = 10000.0 # baseline time in ms

    # 1. State: NO_ACTION (FIST active)
    fist_gesture = GestureClassification(
        gesture_token=GestureToken.FIST,
        c_gesture=0.95,
        requires_gaze_target=False,
        action_intent="NO_ACTION",
        stable_duration_ms=200.0,
        timestamp_ms=t0
    )
    arb_fist, mode_fist = arbiter.arbitrate(fist_gesture, timestamp_ms=t0)
    assert mode_fist == DeviceMode.NO_ACTION
    assert arb_fist.c_gesture == 0.0
    assert arb_fist.action_intent == "NO_ACTION"

    # 2. State: KEYBOARD (Keyboard event happened 200ms ago <= 1500ms)
    arbiter.record_synthetic_event("KEYBOARD", timestamp_ms=t0)
    pinch_gesture = GestureClassification(
        gesture_token=GestureToken.PINCH_INDEX,
        c_gesture=0.88,
        requires_gaze_target=True,
        action_intent="PRIMARY_CLICK",
        stable_duration_ms=100.0,
        timestamp_ms=t0 + 200.0
    )
    arb_kb, mode_kb = arbiter.arbitrate(pinch_gesture, timestamp_ms=t0 + 200.0)
    assert mode_kb == DeviceMode.KEYBOARD
    assert arb_kb.c_gesture == 0.0
    assert arb_kb.action_intent == "NO_ACTION"

    # 3. State: MOUSE_PRIORITY (Mouse event at t=t0+1600ms, keyboard expired)
    arbiter.record_synthetic_event("MOUSE", timestamp_ms=t0 + 1600.0)
    arb_mouse, mode_mouse = arbiter.arbitrate(pinch_gesture, timestamp_ms=t0 + 1800.0)
    assert mode_mouse == DeviceMode.MOUSE_PRIORITY
    # Soft confidence reduction factor = 0.50 * 0.88 = 0.44
    assert abs(arb_mouse.c_gesture - 0.44) < 1e-4
    assert arb_mouse.action_intent == "PRIMARY_CLICK"

    # 4. State: GESTURE (All physical inputs expired, t=t0+3000ms)
    arb_gesture, mode_gesture = arbiter.arbitrate(pinch_gesture, timestamp_ms=t0 + 3000.0)
    assert mode_gesture == DeviceMode.GESTURE
    assert arb_gesture.c_gesture == 0.88
    assert arb_gesture.action_intent == "PRIMARY_CLICK"
