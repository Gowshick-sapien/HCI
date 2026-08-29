"""
Unit tests for HeadPoseEstimator and SolvePnP 3D pose solving.
"""

import numpy as np
import pytest

from src.perception.head_pose_estimator import HeadPoseEstimator


def test_head_pose_estimator_neutral_projection():
    """Verifies that canonical frontal 2D projections produce valid near-frontal yaw, pitch, roll."""
    estimator = HeadPoseEstimator(camera_fov_degrees=60.0)

    w, h = 640, 480
    cx, cy = w / 2.0, h / 2.0

    scale = 0.5
    raw_468 = [(cx, cy, 0.0)] * 468

    # Apply 2D projections of 6 canonical points in standard image coordinates (+Y is down)
    raw_468[HeadPoseEstimator.NOSE_TIP] = (cx + 0.0 * scale, cy + 0.0 * scale, 0.0)
    raw_468[HeadPoseEstimator.CHIN] = (cx + 0.0 * scale, cy + 330.0 * scale, 0.0)
    raw_468[HeadPoseEstimator.LEFT_EYE_OUTER] = (cx - 225.0 * scale, cy - 170.0 * scale, 0.0)
    raw_468[HeadPoseEstimator.RIGHT_EYE_OUTER] = (cx + 225.0 * scale, cy - 170.0 * scale, 0.0)
    raw_468[HeadPoseEstimator.LEFT_MOUTH_CORNER] = (cx - 150.0 * scale, cy + 150.0 * scale, 0.0)
    raw_468[HeadPoseEstimator.RIGHT_MOUTH_CORNER] = (cx + 150.0 * scale, cy + 150.0 * scale, 0.0)

    pose = estimator.estimate(raw_468, frame_width=w, frame_height=h)
    assert pose is not None
    assert abs(pose.yaw) < 25.0
    assert abs(pose.pitch) < 25.0
    assert abs(pose.roll) < 25.0
    assert pose.confidence > 0.30
    assert len(pose.translation_vector) == 3
