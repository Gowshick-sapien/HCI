"""
Frame and Video Capture Types.
Defines data structures and configuration contracts for the video acquisition subsystem.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import time
from typing import Optional
import numpy as np

from src.storage.schemas import RawFrame


@dataclass(frozen=True)
class CameraConfig:
    """Configuration parameters for camera acquisition and buffering."""
    camera_id: int = 0
    frame_width: int = 640
    frame_height: int = 480
    target_fps: int = 30
    ring_buffer_capacity: int = 5
    max_capture_latency_ms: float = 5.0
    use_synthetic_feeder: bool = False


__all__ = ["RawFrame", "CameraConfig"]
