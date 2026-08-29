"""
Integration test for the Layer 1 + Layer 1B + Modality Arbiter pipeline.
"""

import time
import numpy as np
import pytest

from src.capture.frame_types import RawFrame
from src.gesture.gesture_classifier import GestureClassifier
from src.gesture.modality_arbiter import ModalityArbiter
from src.perception.feature_pipeline import FeaturePipeline
from src.storage.schemas import DeviceMode, GestureToken, PerceptionFrame, ProfileSnapshot


def test_end_to_end_perception_integration():
    """Verifies end-to-end frame processing through Perception, Gesture Classification, and Arbitration."""
    pipeline = FeaturePipeline(screen_width=1920, screen_height=1080)
    classifier = GestureClassifier()
    arbiter = ModalityArbiter(enable_pynput_hooks=False)
    profile = ProfileSnapshot.create_default()

    # Create dummy black frame
    dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
    t_now = time.time()
    raw_frame = RawFrame(
        frame_id=1,
        timestamp=t_now,
        width=640,
        height=480,
        ambient_lux=50.0,
        capture_latency_ms=1.2,
        image=dummy_img
    )

    # 1. Execute Layer 1 Feature Pipeline
    perc_frame = pipeline.process_frame(raw_frame, profile=profile)
    assert isinstance(perc_frame, PerceptionFrame)
    assert perc_frame.frame_id == 1
    assert perc_frame.gaze_screen_xy is not None
    assert len(perc_frame.head_euler_angles) == 3

    # 2. Execute Layer 1B Gesture Classifier
    gesture_out = classifier.classify(perc_frame.hand, timestamp_ms=perc_frame.timestamp_ms)
    assert gesture_out.gesture_token in GestureToken

    # 3. Execute Modality Arbiter
    arbitrated_gesture, active_mode = arbiter.arbitrate(gesture_out, timestamp_ms=perc_frame.timestamp_ms)
    assert active_mode in DeviceMode

    pipeline.close()
