"""
Video Acquisition and Ingestion Subsystem.
"""

from src.capture.frame_types import CameraConfig, RawFrame
from src.capture.video_stream import VideoStream

__all__ = ["CameraConfig", "RawFrame", "VideoStream"]
