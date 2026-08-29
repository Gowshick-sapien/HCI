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
