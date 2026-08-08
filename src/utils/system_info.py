"""
System Information, High-Precision Timers and OS Integration Utilities.
Provides cross-platform active window tracking, screen metrics, and CPU profilers.
"""

import os
import platform
import sys
import time
from typing import Optional, Tuple


class HighPrecisionTimer:
    """Context manager and utility for high-precision microsecond-level latency measurement."""

    def __init__(self, name: str = "operation"):
        self.name = name
        self.start_time: float = 0.0
        self.elapsed_ms: float = 0.0

    def __enter__(self) -> "HighPrecisionTimer":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.elapsed_ms = (time.perf_counter() - self.start_time) * 1000.0

    def elapsed(self) -> float:
        """Returns elapsed time in milliseconds."""
        if self.start_time == 0.0:
            return 0.0
        return (time.perf_counter() - self.start_time) * 1000.0


def get_active_window_info() -> Tuple[int, str]:
    """
    Retrieves the PID and Title of the currently focused active OS window.
    Supports Windows via native Win32 APIs with graceful cross-platform fallback.
    """
    os_name = platform.system()
    
    if os_name == "Windows":
        try:
            import ctypes
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            hwnd = user32.GetForegroundWindow()
            if hwnd == 0:
                return 0, "Desktop"

            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value if buff.value else "Unknown Window"

            return int(pid.value), str(title)
        except Exception:
            return 0, "Windows Active Window"
    else:
        return 0, f"{os_name} Active Window"


def get_screen_dimensions() -> Tuple[int, int]:
    """Returns the primary display width and height in pixels (defaults to 1920x1080 if unavailable)."""
    try:
        import pyautogui
        size = pyautogui.size()
        return int(size.width), int(size.height)
    except Exception:
        return 1920, 1080
