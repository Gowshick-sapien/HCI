"""
Integration test for the Layer 2 Calibration -> Profile -> Layer 3 Command Composer flow.
"""

import tempfile
import time
from pathlib import Path
import numpy as np
import pytest

from src.calibration.gaze_calibrator import (
    CalibrationPointSample,
    GazeCalibrator,
)
from src.calibration.head_pose_calibrator import HeadPoseCalibrator
from src.capture.frame_types import RawFrame
from src.fusion.command_composer import CommandComposer
from src.gesture.gesture_classifier import GestureClassifier
from src.perception.feature_pipeline import FeaturePipeline
from src.storage.profile_manager import ProfileManager
from src.storage.schemas import (
    ActionType,
    DeviceMode,
    GestureToken,
    ProfileSnapshot,
)


def test_end_to_end_calibration_to_command_composition():
    with tempfile.TemporaryDirectory() as tmpdir:
        profile_mgr = ProfileManager(profiles_dir=Path(tmpdir))
        user_id = "test_calib_user"

        # 1. Generate 9-Point Calibration Samples
        samples = []
        for tx, ty in [(0.1, 0.1), (0.5, 0.1), (0.9, 0.1), (0.1, 0.5), (0.5, 0.5), (0.9, 0.5), (0.1, 0.9), (0.5, 0.9), (0.9, 0.9)]:
            s = CalibrationPointSample(
                target_screen_xy=(tx * 1920, ty * 1080),
                iris_ratio_x_mean=0.35 + tx * 0.30,
                iris_ratio_y_mean=0.35 + ty * 0.30
            )
            samples.append(s)

        gaze_calibrator = GazeCalibrator(screen_width=1920, screen_height=1080)
        head_calibrator = HeadPoseCalibrator()

        gaze_res = gaze_calibrator.solve(samples)
        head_res = head_calibrator.fit([(0.0, 0.0, 0.0)] * 20)

        # 2. Persist Profile
        profile = ProfileSnapshot.create_default(user_id=user_id)
        profile.gaze_calibration_matrix = [list(row) for row in gaze_res.affine_matrix_3x3]
        profile.neutral_pose_mean = list(head_res.mean_euler_angles)
        profile.neutral_pose_cov_inv = [list(row) for row in head_res.precision_matrix_3x3]

        assert profile_mgr.save_profile(profile) is True

        # 3. Ingest via FeaturePipeline & Command Composer
        loaded_profile = profile_mgr.load_profile(user_id)
        pipeline = FeaturePipeline()
        classifier = GestureClassifier()
        composer = CommandComposer()

        dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
        raw_frame = RawFrame(frame_id=1, timestamp=time.time(), width=640, height=480, ambient_lux=50.0, capture_latency_ms=1.0, image=dummy_img)

        perc_frame = pipeline.process_frame(raw_frame, profile=loaded_profile)
        gesture_out = classifier.classify(perc_frame.hand, timestamp_ms=perc_frame.timestamp_ms)
        composed_cmd = composer.compose(perc_frame, gesture_out, profile=loaded_profile)

        assert composed_cmd is not None
        assert composed_cmd.action_type in ActionType
        pipeline.close()
