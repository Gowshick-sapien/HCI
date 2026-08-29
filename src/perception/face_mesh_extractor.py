"""
FaceMesh and Refined Iris Feature Extractor.
Uses MediaPipe FaceMesh (refine_landmarks=True) to extract 468 facial landmarks,
10 iris landmark coordinates, compute Eye Aspect Ratio (EAR), and estimate gaze pupil ratios.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple
import cv2
import mediapipe as mp
import numpy as np

from src.storage.schemas import EyeLandmarks

logger = logging.getLogger(__name__)


class FaceMeshExtractor:
    """
    MediaPipe FaceMesh wrapper with refined 10-point iris tracking.
    Computes ocular gaze offsets and blink detection metrics in real time.
    """

    # Correct MediaPipe FaceMesh Landmark Indices
    # Eye 1 (Viewer's Left, Person's Right Eye):
    RIGHT_IRIS_CENTER = 468
    RIGHT_EYE_OUTER = 33
    RIGHT_EYE_INNER = 133
    RIGHT_EYE_TOP = 159
    RIGHT_EYE_BOTTOM = 145
    RIGHT_EYE_EAR_PTS = [33, 160, 158, 133, 153, 144]

    # Eye 2 (Viewer's Right, Person's Left Eye):
    LEFT_IRIS_CENTER = 473
    LEFT_EYE_INNER = 362
    LEFT_EYE_OUTER = 263
    LEFT_EYE_TOP = 386
    LEFT_EYE_BOTTOM = 374
    LEFT_EYE_EAR_PTS = [263, 387, 385, 362, 380, 373]

    def __init__(
        self,
        max_num_faces: int = 1,
        refine_landmarks: bool = True,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        ear_blink_threshold: float = 0.18
    ) -> None:
        self.max_num_faces = max_num_faces
        self.refine_landmarks = refine_landmarks
        self.min_detection_confidence = float(min_detection_confidence)
        self.min_tracking_confidence = float(min_tracking_confidence)
        self.ear_blink_threshold = float(ear_blink_threshold)

        self._mp_face_mesh = mp.solutions.face_mesh
        self._face_mesh = self._mp_face_mesh.FaceMesh(
            max_num_faces=self.max_num_faces,
            refine_landmarks=self.refine_landmarks,
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence
        )

    def extract(self, image_bgr: np.ndarray) -> Tuple[Optional[EyeLandmarks], Optional[List[Tuple[float, float, float]]]]:
        """
        Processes a single BGR video frame to extract eye landmarks and 3D facial mesh coordinates.
        """
        if image_bgr is None or image_bgr.size == 0:
            return None, None

        h, w = image_bgr.shape[:2]
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False

        results = self._face_mesh.process(image_rgb)

        if not results.multi_face_landmarks:
            return None, None

        face_landmarks = results.multi_face_landmarks[0]
        raw_pts = [(lm.x * w, lm.y * h, lm.z * w) for lm in face_landmarks.landmark]

        if len(raw_pts) < 478:
            return None, raw_pts

        # 1. Compute EAR for blink suppression
        right_ear = self._compute_ear(raw_pts, self.RIGHT_EYE_EAR_PTS)
        left_ear = self._compute_ear(raw_pts, self.LEFT_EYE_EAR_PTS)
        avg_ear = (left_ear + right_ear) / 2.0

        is_blinking = avg_ear < self.ear_blink_threshold

        # 2. Extract Iris Centers in pixel space
        right_iris_xy = (raw_pts[self.RIGHT_IRIS_CENTER][0], raw_pts[self.RIGHT_IRIS_CENTER][1])
        left_iris_xy = (raw_pts[self.LEFT_IRIS_CENTER][0], raw_pts[self.LEFT_IRIS_CENTER][1])

        # 3. Compute Normalized Gaze Ratios relative to each eye's own corner bounding box
        rx_r, ry_r = self._compute_iris_ratio(
            raw_pts, self.RIGHT_IRIS_CENTER, self.RIGHT_EYE_INNER, self.RIGHT_EYE_OUTER,
            self.RIGHT_EYE_TOP, self.RIGHT_EYE_BOTTOM
        )
        rx_l, ry_l = self._compute_iris_ratio(
            raw_pts, self.LEFT_IRIS_CENTER, self.LEFT_EYE_INNER, self.LEFT_EYE_OUTER,
            self.LEFT_EYE_TOP, self.LEFT_EYE_BOTTOM
        )

        iris_ratio_x = float(np.clip((rx_r + rx_l) / 2.0, 0.0, 1.0))
        iris_ratio_y = float(np.clip((ry_r + ry_l) / 2.0, 0.0, 1.0))

        # Confidence: 0.0 if blinking, else based on tracking quality
        if is_blinking:
            confidence = 0.0
        else:
            confidence = float(np.clip((avg_ear - self.ear_blink_threshold) / 0.10, 0.40, 1.0))

        eye_data = EyeLandmarks(
            left_iris_center=left_iris_xy,
            right_iris_center=right_iris_xy,
            left_ear=float(left_ear),
            right_ear=float(right_ear),
            iris_ratio_x=iris_ratio_x,
            iris_ratio_y=iris_ratio_y,
            confidence=confidence,
            variance=0.04 if not is_blinking else 0.50
        )

        return eye_data, raw_pts

    @staticmethod
    def _compute_ear(pts: List[Tuple[float, float, float]], indices: List[int]) -> float:
        """Computes Eye Aspect Ratio from 6 landmark indices."""
        try:
            p1 = np.array(pts[indices[0]][:2])
            p2 = np.array(pts[indices[1]][:2])
            p3 = np.array(pts[indices[2]][:2])
            p4 = np.array(pts[indices[3]][:2])
            p5 = np.array(pts[indices[4]][:2])
            p6 = np.array(pts[indices[5]][:2])

            v1 = np.linalg.norm(p2 - p6)
            v2 = np.linalg.norm(p3 - p5)
            horiz = np.linalg.norm(p1 - p4)

            if horiz < 1e-4:
                return 0.25
            return float((v1 + v2) / (2.0 * horiz))
        except Exception:
            return 0.25

    @staticmethod
    def _compute_iris_ratio(
        pts: List[Tuple[float, float, float]],
        iris_idx: int,
        inner_idx: int,
        outer_idx: int,
        top_idx: int,
        bottom_idx: int
    ) -> Tuple[float, float]:
        """Calculates normalized position of the iris within its own eye corner bounding box."""
        try:
            iris_x, iris_y = pts[iris_idx][0], pts[iris_idx][1]
            inner_x, inner_y = pts[inner_idx][0], pts[inner_idx][1]
            outer_x, outer_y = pts[outer_idx][0], pts[outer_idx][1]
            top_x, top_y = pts[top_idx][0], pts[top_idx][1]
            bottom_x, bottom_y = pts[bottom_idx][0], pts[bottom_idx][1]

            min_x, max_x = min(inner_x, outer_x), max(inner_x, outer_x)
            min_y, max_y = min(top_y, bottom_y), max(top_y, bottom_y)

            dx = max_x - min_x
            dy = max_y - min_y

            rx = (iris_x - min_x) / dx if dx > 1.0 else 0.5
            ry = (iris_y - min_y) / dy if dy > 1.0 else 0.5

            return float(np.clip(rx, 0.0, 1.0)), float(np.clip(ry, 0.0, 1.0))
        except Exception:
            return 0.5, 0.5

    def close(self) -> None:
        """Releases underlying MediaPipe FaceMesh resources."""
        if hasattr(self, "_face_mesh") and self._face_mesh:
            self._face_mesh.close()


__all__ = ["FaceMeshExtractor"]
