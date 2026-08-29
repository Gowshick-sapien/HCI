"""
Active Modality Arbiter.
Monitors low-level physical keyboard and mouse activity to enforce priority-ordered arbitration,
proactively suppressing gesture evaluation during manual typing and mouse navigation.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Optional, Tuple

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
        enable_pynput_hooks: bool = True
    ) -> None:
        self.keyboard_timeout_ms = float(keyboard_timeout_ms)
        self.mouse_timeout_ms = float(mouse_timeout_ms)
        self.soft_reduction_factor = float(soft_reduction_factor)
        self.enable_pynput_hooks = enable_pynput_hooks

        # Last activity timestamps (in milliseconds)
        self._last_keyboard_timestamp_ms: float = 0.0
        self._last_mouse_timestamp_ms: float = 0.0
        self._prev_mouse_xy: Optional[Tuple[int, int]] = None
        self._lock = threading.Lock()

        # Listener objects
        self._keyboard_listener = None
        self._mouse_listener = None
        self._is_listening: bool = False

    def start_listeners(self) -> bool:
        """Starts asynchronous non-blocking background input listeners if enabled."""
        if not self.enable_pynput_hooks or self._is_listening:
            return True

        try:
            from pynput import keyboard, mouse

            def on_key_press(key):
                with self._lock:
                    self._last_keyboard_timestamp_ms = time.time() * 1000.0

            def on_mouse_move(x, y):
                with self._lock:
                    if self._prev_mouse_xy is not None:
                        dx = x - self._prev_mouse_xy[0]
                        dy = y - self._prev_mouse_xy[1]
                        # Filter out sub-pixel jitter; require deliberate mouse motion >= 4 px
                        if (dx * dx + dy * dy) >= 16:
                            self._last_mouse_timestamp_ms = time.time() * 1000.0
                            self._prev_mouse_xy = (x, y)
                    else:
                        self._prev_mouse_xy = (x, y)

            def on_mouse_click(x, y, button, pressed):
                if pressed:
                    with self._lock:
                        self._last_mouse_timestamp_ms = time.time() * 1000.0

            self._keyboard_listener = keyboard.Listener(on_press=on_key_press)
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

    def get_current_device_mode(
        self,
        current_gesture: Optional[GestureToken] = None,
        timestamp_ms: Optional[float] = None
    ) -> DeviceMode:
        """
        Evaluates current physical device mode based on priority rules.
        """
        t_now = timestamp_ms if timestamp_ms is not None else (time.time() * 1000.0)

        # 1. Hard FIST REST Guard overrides everything to NO_ACTION
        if current_gesture == GestureToken.FIST:
            return DeviceMode.NO_ACTION

        with self._lock:
            dt_key = t_now - self._last_keyboard_timestamp_ms
            dt_mouse = t_now - self._last_mouse_timestamp_ms

        # 2. Priority 1: Physical Keyboard Active
        if dt_key >= 0.0 and dt_key <= self.keyboard_timeout_ms:
            return DeviceMode.KEYBOARD

        # 3. Priority 2: Physical Mouse Active
        if dt_mouse >= 0.0 and dt_mouse <= self.mouse_timeout_ms:
            return DeviceMode.MOUSE_PRIORITY

        # 4. Priority 3: Multimodal Gesture Uninhibited
        return DeviceMode.GESTURE

    def arbitrate(
        self,
        gesture: GestureClassification,
        timestamp_ms: Optional[float] = None
    ) -> Tuple[GestureClassification, DeviceMode]:
        """
        Applies arbitration rules to the incoming gesture classification.

        Returns:
            (arbitrated_gesture, active_device_mode)
        """
        mode = self.get_current_device_mode(
            current_gesture=gesture.gesture_token,
            timestamp_ms=timestamp_ms
        )

        if mode == DeviceMode.NO_ACTION:
            # Complete suppression
            arbitrated = GestureClassification(
                gesture_token=gesture.gesture_token,
                c_gesture=0.0,
                requires_gaze_target=gesture.requires_gaze_target,
                action_intent="NO_ACTION",
                stable_duration_ms=gesture.stable_duration_ms,
                timestamp_ms=gesture.timestamp_ms
            )
        elif mode == DeviceMode.KEYBOARD:
            # Suppress gesture while user is typing
            arbitrated = GestureClassification(
                gesture_token=GestureToken.NONE,
                c_gesture=0.0,
                requires_gaze_target=False,
                action_intent="NO_ACTION",
                stable_duration_ms=0.0,
                timestamp_ms=gesture.timestamp_ms
            )
        elif mode == DeviceMode.MOUSE_PRIORITY:
            # Soft confidence reduction
            arbitrated = GestureClassification(
                gesture_token=gesture.gesture_token,
                c_gesture=float(gesture.c_gesture * self.soft_reduction_factor),
                requires_gaze_target=gesture.requires_gaze_target,
                action_intent=gesture.action_intent,
                stable_duration_ms=gesture.stable_duration_ms,
                timestamp_ms=gesture.timestamp_ms
            )
        else:
            # GESTURE mode: uninhibited
            arbitrated = gesture

        return arbitrated, mode


__all__ = ["ModalityArbiter"]
