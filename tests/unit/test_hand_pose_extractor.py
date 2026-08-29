"""
Unit tests for HandPoseExtractor kinematics and curl calculations.
"""

import numpy as np
import pytest

from src.perception.hand_pose_extractor import HandPoseExtractor


def test_hand_pose_finger_curl_computation():
    extractor = HandPoseExtractor()

    # Synthetic straight extended index finger:
    # MCP=(0,0,0), PIP=(0,1,0), DIP=(0,2,0), TIP=(0,3,0)
    # Direct = 3, Segments = 1+1+1=3 => Curl = 1.0 - (3/3) = 0.0
    pts_straight = np.zeros((21, 3), dtype=np.float64)
    pts_straight[5] = [0.0, 0.0, 0.0]
    pts_straight[6] = [0.0, 1.0, 0.0]
    pts_straight[7] = [0.0, 2.0, 0.0]
    pts_straight[8] = [0.0, 3.0, 0.0]

    curls_straight = extractor._compute_finger_curls(pts_straight)
    assert abs(curls_straight["index"] - 0.0) < 1e-4

    # Synthetic tightly curled finger:
    # MCP=(0,0,0), PIP=(0,1,0), DIP=(0.5, 0.5, 0), TIP=(0.1, 0.1, 0)
    # Direct distance TIP-MCP ~= 0.14, Segments = 1.0 + 0.707 + 0.565 = 2.27 => Curl ~= 0.938
    pts_curled = np.zeros((21, 3), dtype=np.float64)
    pts_curled[5] = [0.0, 0.0, 0.0]
    pts_curled[6] = [0.0, 1.0, 0.0]
    pts_curled[7] = [0.5, 0.5, 0.0]
    pts_curled[8] = [0.1, 0.1, 0.0]

    curls_curled = extractor._compute_finger_curls(pts_curled)
    assert curls_curled["index"] >= 0.85
