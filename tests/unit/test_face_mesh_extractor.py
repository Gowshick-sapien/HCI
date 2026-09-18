"""
Unit tests for FaceMesh and iris extraction logic.
"""

import numpy as np
import pytest

from src.perception.face_mesh_extractor import FaceMeshExtractor


def test_face_mesh_extractor_ear_calculation():
    """Invariant INV-D1.3: Verifies EAR blink detection math."""
    # Synthetic eye points for open eye
    # p1=(0,0), p2=(2, 2), p3=(4, 2), p4=(6, 0), p5=(4, -2), p6=(2, -2)
    # v1 = norm((2,2)-(2,-2)) = 4
    # v2 = norm((4,2)-(4,-2)) = 4
    # horiz = norm((0,0)-(6,0)) = 6
    # EAR = (4 + 4) / (2 * 6) = 8 / 12 = 0.667
    pts = [
        (0.0, 0.0, 0.0),    # 0 (p1)
        (2.0, 2.0, 0.0),    # 1 (p2)
        (4.0, 2.0, 0.0),    # 2 (p3)
        (6.0, 0.0, 0.0),    # 3 (p4)
        (4.0, -2.0, 0.0),   # 4 (p5)
        (2.0, -2.0, 0.0),   # 5 (p6)
    ]
    indices = [0, 1, 2, 3, 4, 5]
    ear_open = FaceMeshExtractor._compute_ear(pts, indices)
    assert abs(ear_open - 0.667) < 0.01

    # Synthetic eye points for closed eye (blinking)
    pts_closed = [
        (0.0, 0.0, 0.0),
        (2.0, 0.2, 0.0),
        (4.0, 0.2, 0.0),
        (6.0, 0.0, 0.0),
        (4.0, -0.2, 0.0),
        (2.0, -0.2, 0.0),
    ]
    ear_closed = FaceMeshExtractor._compute_ear(pts_closed, indices)
    # EAR = (0.4 + 0.4) / (2 * 6) = 0.8 / 12 = 0.0667 (< 0.18)
    assert ear_closed < 0.18


def test_face_mesh_extractor_iris_ratio():
    # Pupil at center of eye box
    pts = [
        (100.0, 100.0, 0.0), # 0: inner (x=100, y=100)
        (200.0, 100.0, 0.0), # 1: outer (x=200, y=100)
        (150.0, 80.0, 0.0),  # 2: top (y=80)
        (150.0, 120.0, 0.0), # 3: bottom (y=120)
        (150.0, 100.0, 0.0), # 4: iris center
    ]
    rx, ry = FaceMeshExtractor._compute_iris_ratio(pts, 4, 0, 1, 2, 3)
    assert abs(rx - 0.50) < 0.01
    assert abs(ry - 0.50) < 0.01

def test_face_mesh_extractor_iris_ratio_is_roll_and_eyelid_invariant():
    # A 90-degree roll and a different eyelid aperture preserve the canthus
    # coordinates because the eye-width baseline, rather than lid height, scales y.
    flat_eye = [
        (0.0, 0.0, 0.0), (100.0, 0.0, 0.0), (50.0, -20.0, 0.0),
        (50.0, 20.0, 0.0), (75.0, 10.0, 0.0),
    ]
    rolled_squint = [
        (0.0, 0.0, 0.0), (0.0, 100.0, 0.0), (10.0, 50.0, 0.0),
        (-10.0, 50.0, 0.0), (-10.0, 75.0, 0.0),
    ]

    rx_a, ry_a = FaceMeshExtractor._compute_iris_ratio(flat_eye, 4, 0, 1, 2, 3, is_right_eye=False)
    rx_b, ry_b = FaceMeshExtractor._compute_iris_ratio(rolled_squint, 4, 0, 1, 2, 3, is_right_eye=False)

    assert np.allclose((rx_a, ry_a), (rx_b, ry_b), atol=1e-6)


def test_face_mesh_extractor_right_eye_anatomical_direction():
    # Person's right eye: inner landmark is camera-right of outer landmark
    # outer=(0, 100), inner=(100, 100). Midpoint is 50.
    pts = [
        (100.0, 100.0, 0.0),  # 0: inner canthus
        (0.0, 100.0, 0.0),    # 1: outer canthus
        (50.0, 80.0, 0.0),    # 2: top
        (50.0, 120.0, 0.0),   # 3: bottom
        (25.0, 100.0, 0.0),   # 4: iris looking camera-left (user's right)
    ]
    rx, ry = FaceMeshExtractor._compute_iris_ratio(pts, 4, 0, 1, 2, 3, is_right_eye=True)
    # Looking user's right (camera-left) means rx decreases below 0.5
    assert rx < 0.50
    assert abs(ry - 0.50) < 0.01

