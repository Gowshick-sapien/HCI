"""
Unit tests for VideoStream and frame ingestion.
"""

import time
import numpy as np
import pytest

from src.capture.frame_types import CameraConfig, RawFrame
from src.capture.video_stream import VideoStream


def test_video_stream_synthetic_feeder():
    """Verifies that synthetic frames can be fed and retrieved without hardware camera."""
    config = CameraConfig(use_synthetic_feeder=True, frame_width=640, frame_height=480, target_fps=30)
    stream = VideoStream(config)

    assert not stream.is_running
    assert stream.start() is True
    assert stream.is_running is True

    # Feed synthetic frame
    dummy_img = np.ones((480, 640, 3), dtype=np.uint8) * 128
    t_inject = time.time()
    fed_frame = stream.feed_synthetic_frame(dummy_img, timestamp=t_inject)

    assert fed_frame.frame_id == 1
    assert fed_frame.width == 640
    assert fed_frame.height == 480
    assert fed_frame.ambient_lux > 0.0

    # Retrieve frame
    retrieved = stream.read_latest_frame(wait_timeout_sec=0.1)
    assert retrieved is not None
    assert retrieved.frame_id == 1
    assert retrieved.image.shape == (480, 640, 3)

    stats = stream.get_stats()
    assert stats["total_captured"] == 1
    assert stats["is_running"] is True

    stream.stop()
    assert not stream.is_running
