"""
Hand Pose Kinematics Extractor.
Uses MediaPipe Hands to extract 21 3D landmark coordinates per hand,
compute wrist velocity, inter-finger tip pinch distances, palm normals, and finger curl ratios.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple
import cv2
import mediapipe as mp
import numpy as np

from src.storage.schemas import HandLandmarks

logger = logging.getLogger(__name__)


class HandPoseExtractor:
    """
    MediaPipe Hands 21-point kinematic tracker.
    Computes spatial hand tracking metrics without assigning domain command semantics.
    """

    # Landmark index definitions
    WRIST = 0
    THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP = 1, 2, 3, 4
    INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP = 5, 6, 7, 8
    MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP = 9, 10, 11, 12
    RING_MCP, RING_PIP, RING_DIP, RING_TIP = 13, 14, 15, 16
    PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP = 17, 18, 19, 20

    FINGER_CHAINS = {
        "index": (INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP),
        "middle": (MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP),
        "ring": (RING_MCP, RING_PIP, RING_DIP, RING_TIP),
        "pinky": (PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP),
    }

    def __init__(
        self,
        max_num_hands: int = 2,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        pinch_threshold_normalized: float = 0.08
    ) -> None:
        self.max_num_hands = max_num_hands
        self.min_detection_confidence = float(min_detection_confidence)
        self.min_tracking_confidence = float(min_tracking_confidence)
        self.pinch_threshold_normalized = float(pinch_threshold_normalized)

        self._mp_hands = mp.solutions.hands
        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=self.max_num_hands,
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence
        )

        # Historical state for velocity estimation
        self._prev_wrist_pos: Optional[np.ndarray] = None
        self._prev_timestamp: Optional[float] = None

    def reset(self) -> None:
        """Resets tracking history."""
        self._prev_wrist_pos = None
        self._prev_timestamp = None

    def extract(
        self,
        image_bgr: np.ndarray,
        timestamp_sec: Optional[float] = None
    ) -> HandLandmarks:
        """
        Extracts 21 3D landmarks and kinematic properties from the current video frame.
        """
        if image_bgr is None or image_bgr.size == 0:
            return self._empty_hand_landmarks()

        h, w = image_bgr.shape[:2]
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False

        results = self._hands.process(image_rgb)

        if not results.multi_hand_landmarks:
            self._prev_wrist_pos = None
            return self._empty_hand_landmarks()

        # Select primary dominant hand (highest landmark certainty or first detected)
        hand_lms = results.multi_hand_landmarks[0]
        landmarks_21 = [(lm.x, lm.y, lm.z) for lm in hand_lms.landmark]
        pts = np.array(landmarks_21, dtype=np.float64)

        # 1. Wrist position & instantaneous velocity
        wrist_pos = pts[self.WRIST]
        wrist_velocity = 0.0
        if self._prev_wrist_pos is not None and timestamp_sec is not None and self._prev_timestamp is not None:
            dt = max(1e-4, timestamp_sec - self._prev_timestamp)
            wrist_velocity = float(np.linalg.norm(wrist_pos - self._prev_wrist_pos) / dt)

        self._prev_wrist_pos = wrist_pos.copy()
        self._prev_timestamp = timestamp_sec

        # 2. Pinch distance (Thumb tip to Index tip in normalized coords)
        thumb_tip = pts[self.THUMB_TIP]
        index_tip = pts[self.INDEX_TIP]
        pinch_dist = float(np.linalg.norm(thumb_tip - index_tip))

        # 3. Palm Normal Vector
        v_across = pts[self.PINKY_MCP] - pts[self.INDEX_MCP]
        v_up = pts[self.MIDDLE_MCP] - pts[self.WRIST]
        normal = np.cross(v_across, v_up)
        norm_val = np.linalg.norm(normal)
        if norm_val > 1e-6:
            normal = normal / norm_val
        else:
            normal = np.array([0.0, 0.0, 1.0])
        palm_normal = (float(normal[0]), float(normal[1]), float(normal[2]))

        # 4. Multi-finger curl ratios
        curl_ratios = self._compute_finger_curls(pts)
        all_curled = all(c >= 0.65 for c in curl_ratios.values())

        confidence = 0.90 if not all_curled else 0.85

        return HandLandmarks(
            is_detected=True,
            pinch_distance=pinch_dist,
            palm_normal=palm_normal,
            wrist_position=(float(wrist_pos[0]), float(wrist_pos[1]), float(wrist_pos[2])),
            wrist_velocity=wrist_velocity,
            gesture_class="HAND_DETECTED",
            confidence=confidence,
            variance=0.04,
            raw_landmarks_21=landmarks_21
        )

    def _compute_finger_curls(self, pts: np.ndarray) -> Dict[str, float]:
        """
        Computes normalized curl ratio for index, middle, ring, and pinky fingers.
        """
        curls = {}
        for finger_name, (mcp, pip, dip, tip) in self.FINGER_CHAINS.items():
            p_mcp = pts[mcp]
            p_pip = pts[pip]
            p_dip = pts[dip]
            p_tip = pts[tip]

            d_direct = np.linalg.norm(p_tip - p_mcp)
            d_segments = (
                np.linalg.norm(p_pip - p_mcp) +
                np.linalg.norm(p_dip - p_pip) +
                np.linalg.norm(p_tip - p_dip)
            )

            if d_segments < 1e-4:
                curl = 0.0
            else:
                curl = float(np.clip(1.0 - (d_direct / d_segments), 0.0, 1.0))

            curls[finger_name] = curl
        return curls

    @staticmethod
    def _empty_hand_landmarks() -> HandLandmarks:
        """Returns default empty HandLandmarks object when no hand is detected."""
        return HandLandmarks(
            is_detected=False,
            pinch_distance=1.0,
            palm_normal=(0.0, 0.0, 1.0),
            wrist_position=(0.0, 0.0, 0.0),
            wrist_velocity=0.0,
            gesture_class="NONE",
            confidence=0.0,
            variance=0.50,
            raw_landmarks_21=None
        )

    def close(self) -> None:
        """Releases underlying MediaPipe Hands resources."""
        if hasattr(self, "_hands") and self._hands:
            self._hands.close()


__all__ = ["HandPoseExtractor"]
