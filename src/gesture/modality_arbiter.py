"""
Active Modality Arbiter.
Monitors low-level physical keyboard and mouse activity to enforce priority-ordered arbitration,
proactively suppressing gesture evaluation during manual typing and mouse navigation.
"""

from __future__ import annotations

import collections
import logging
import threading
import time
from typing import Callable, Deque, List, Optional, Tuple

from src.storage.schemas import DeviceMode, GestureClassification, GestureToken

logger = logging.getLogger(__name__)


class ModalityArbiter:
    """
    Physical input monitor and priority modality arbiter.
    Prevents Midas Touch and conflict between gestures and physical hardware.
    """

    def __init__(
        self,
        keyboard_timeout_ms: float = 1500.0,
        mouse_timeout_ms: float = 800.0,
        soft_reduction_factor: float = 0.50,
        enable_pynput_hooks: bool = True,
        **kwargs
    ) -> None:
        self.keyboard_lockout_ms = float(kwargs.get("keyboard_lockout_ms", keyboard_timeout_ms))
        self.mouse_lockout_ms = float(kwargs.get("mouse_lockout_ms", mouse_timeout_ms))
        self.soft_reduction_factor = float(soft_reduction_factor)
        self.enable_pynput_hooks = enable_pynput_hooks

        self._last_keyboard_timestamp_ms: float = 0.0
        self._last_mouse_timestamp_ms: float = 0.0
        self._prev_mouse_xy: Optional[Tuple[int, int]] = None
        self._lock = threading.RLock()

        self._keyboard_listener = None
        self._mouse_listener = None
        self._is_listening: bool = False

        self._is_ctrl_down: bool = False
        self._accum_mouse_dx: float = 0.0
        self._accum_mouse_dy: float = 0.0
        self._pending_keys: Deque[Tuple[str, bool]] = collections.deque(maxlen=30)

    def pop_accumulated_mouse_delta(self) -> Tuple[float, float]:
        """Returns and resets accumulated physical mouse displacement since last check."""
        with self._lock:
            dx, dy = self._accum_mouse_dx, self._accum_mouse_dy
            self._accum_mouse_dx = 0.0
            self._accum_mouse_dy = 0.0
            return dx, dy

    def pop_pending_key_events(self) -> List[Tuple[str, bool]]:
        """Returns and clears all pending key events recorded by the hook."""
        with self._lock:
            keys = list(self._pending_keys)
            self._pending_keys.clear()
            return keys

    def start_listeners(self) -> bool:
        """
        Starts pynput background threads for mouse and keyboard monitoring.
        """
        if not self.enable_pynput_hooks or self._is_listening:
            return True

        try:
            from pynput import keyboard, mouse

            def on_key_press(key):
                with self._lock:
                    self._last_keyboard_timestamp_ms = time.time() * 1000.0
                    try:
                        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
                            self._is_ctrl_down = True
                        key_name = getattr(key, 'char', None) or str(key)
                        self._pending_keys.append((key_name, self._is_ctrl_down))
                    except Exception:
                        pass

            def on_key_release(key):
                with self._lock:
                    if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
                        self._is_ctrl_down = False

            def on_mouse_move(x, y):
                with self._lock:
                    if self._prev_mouse_xy is not None:
                        dx = x - self._prev_mouse_xy[0]
                        dy = y - self._prev_mouse_xy[1]
                        # Filter out sub-pixel jitter; require deliberate mouse motion >= 4 px
                        if (dx * dx + dy * dy) >= 16:
                            self._last_mouse_timestamp_ms = time.time() * 1000.0
                            self._prev_mouse_xy = (x, y)
                            self._accum_mouse_dx += dx
                            self._accum_mouse_dy += dy
                    else:
                        self._prev_mouse_xy = (x, y)

            def on_mouse_click(x, y, button, pressed):
                if pressed:
                    with self._lock:
                        self._last_mouse_timestamp_ms = time.time() * 1000.0

            self._keyboard_listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
            self._mouse_listener = mouse.Listener(on_move=on_mouse_move, on_click=on_mouse_click)

            self._keyboard_listener.daemon = True
            self._mouse_listener.daemon = True

            self._keyboard_listener.start()
            self._mouse_listener.start()
            self._is_listening = True
            logger.info("ModalityArbiter physical device listeners successfully started.")
            return True
        except Exception as e:
            logger.warning(f"Failed to initialize pynput physical device listeners: {e}. Falling back to passive mode.")
            self._is_listening = False
            return False

    def stop_listeners(self) -> None:
        """Stops active input listeners."""
        if self._keyboard_listener is not None:
            try:
                self._keyboard_listener.stop()
            except Exception:
                pass
            self._keyboard_listener = None

        if self._mouse_listener is not None:
            try:
                self._mouse_listener.stop()
            except Exception:
                pass
            self._mouse_listener = None

        self._is_listening = False

    def record_synthetic_event(self, device: str, timestamp_ms: Optional[float] = None) -> None:
        """
        Manually injects physical device activity for testing and simulations.
        """
        t = timestamp_ms if timestamp_ms is not None else (time.time() * 1000.0)
        with self._lock:
            if device.upper() == "KEYBOARD":
                self._last_keyboard_timestamp_ms = t
            elif device.upper() == "MOUSE":
                self._last_mouse_timestamp_ms = t

    def arbitrate(
        self,
        gesture: GestureClassification,
        timestamp_ms: Optional[float] = None
    ) -> Tuple[GestureClassification, DeviceMode]:
        """
        Arbitrates active input device modality and filters gestures.
        """
        now = timestamp_ms if timestamp_ms is not None else (time.time() * 1000.0)

        with self._lock:
            dt_kb = now - self._last_keyboard_timestamp_ms
            dt_mouse = now - self._last_mouse_timestamp_ms

        # Priority 1: Physical Keyboard active -> Complete suppression of gesture interaction
        if 0.0 <= dt_kb < self.keyboard_lockout_ms:
            suppressed_gesture = GestureClassification(
                gesture_token=GestureToken.FIST,
                c_gesture=0.0,
                requires_gaze_target=False,
                action_intent="NO_ACTION",
                stable_duration_ms=0.0,
                timestamp_ms=now
            )
            return suppressed_gesture, DeviceMode.KEYBOARD

        # Priority 2: Physical Mouse active -> Soft reduction of gesture confidence
        if 0.0 <= dt_mouse < self.mouse_lockout_ms:
            reduced_gesture = GestureClassification(
                gesture_token=gesture.gesture_token,
                c_gesture=float(gesture.c_gesture * self.soft_reduction_factor),
                requires_gaze_target=gesture.requires_gaze_target,
                action_intent=gesture.action_intent,
                stable_duration_ms=gesture.stable_duration_ms,
                timestamp_ms=now
            )
            return reduced_gesture, DeviceMode.MOUSE_PRIORITY

        # Priority 3: Multimodal Gesture active
        if gesture.gesture_token not in (GestureToken.NONE, GestureToken.FIST) and gesture.c_gesture > 0.0:
            return gesture, DeviceMode.GESTURE

        # Idle state (FIST / NONE)
        idle_gesture = GestureClassification(
            gesture_token=GestureToken.FIST,
            c_gesture=0.0,
            requires_gaze_target=False,
            action_intent="NO_ACTION",
            stable_duration_ms=0.0,
            timestamp_ms=now
        )
        return idle_gesture, DeviceMode.NO_ACTION


__all__ = ["ModalityArbiter"]
