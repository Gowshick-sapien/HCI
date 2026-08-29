"""
Kinematic Gesture Classifier & FIST Guard.
Translates 21-point hand tracking kinematics into 13 named gesture tokens with sigmoid confidence.
Enforces the hard FIST REST guard for Midas Touch suppression.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import numpy as np

from src.gesture.gesture_vocabulary import GestureVocabulary
from src.storage.schemas import GestureClassification, GestureToken, HandLandmarks
from src.utils.math_utils import sigmoid


class GestureClassifier:
    """
    Real-time kinematic gesture classifier with scale-invariant palm normalization
    and temporal stabilization.
    """

    # Hand landmark indices
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
        vocabulary: Optional[GestureVocabulary] = None,
        default_pinch_threshold: float = 0.085,
        fist_curl_threshold: float = 0.58,
        pinch_hold_duration_ms: float = 500.0
    ) -> None:
        self.vocabulary = vocabulary or GestureVocabulary()
        self.default_pinch_threshold = float(default_pinch_threshold)
        self.fist_curl_threshold = float(fist_curl_threshold)
        self.pinch_hold_duration_ms = float(pinch_hold_duration_ms)

        # Temporal stabilization state
        self._current_token: GestureToken = GestureToken.NONE
        self._stable_duration_ms: float = 0.0
        self._last_timestamp_ms: Optional[float] = None
        self._prev_wrist_pos: Optional[Tuple[float, float, float]] = None

    def reset(self) -> None:
        """Resets temporal gesture stability timers."""
        self._current_token = GestureToken.NONE
        self._stable_duration_ms = 0.0
        self._last_timestamp_ms = None
        self._prev_wrist_pos = None

    def classify(
        self,
        hand: HandLandmarks,
        timestamp_ms: float,
        personalized_thresholds: Optional[Dict[str, float]] = None
    ) -> GestureClassification:
        """
        Classifies current hand kinematics into a named GestureClassification token.
        """
        delta_t = (timestamp_ms - self._last_timestamp_ms) if self._last_timestamp_ms is not None else 33.3
        delta_t = max(0.0, min(delta_t, 100.0))
        self._last_timestamp_ms = timestamp_ms

        if not hand.is_detected or not hand.raw_landmarks_21 or len(hand.raw_landmarks_21) < 21:
            self._update_stable_duration(GestureToken.NONE, delta_t)
            return GestureClassification(
                gesture_token=GestureToken.NONE,
                c_gesture=0.0,
                requires_gaze_target=False,
                action_intent="NO_ACTION",
                stable_duration_ms=self._stable_duration_ms,
                timestamp_ms=timestamp_ms
            )

        pts = np.array(hand.raw_landmarks_21, dtype=np.float64)
        curls = self._compute_finger_curls(pts)

        # Compute scale-invariant palm dimension (wrist to middle MCP)
        palm_size = float(np.linalg.norm(pts[self.MIDDLE_MCP] - pts[self.WRIST]))
        palm_size = max(0.06, min(palm_size, 0.45))
        scale_factor = palm_size / 0.18

        thumb_tip = pts[self.THUMB_TIP]
        thumb_ip = pts[self.THUMB_IP]
        thumb_mcp = pts[self.THUMB_MCP]
        index_mcp = pts[self.INDEX_MCP]
        index_tip = pts[self.INDEX_TIP]
        middle_tip = pts[self.MIDDLE_TIP]
        ring_tip = pts[self.RING_TIP]
        pinky_tip = pts[self.PINKY_TIP]

        all_curled = all(curls[f] >= self.fist_curl_threshold for f in ["index", "middle", "ring", "pinky"])

        # -------------------------------------------------------------
        # 1. FIST REST GUARD & THUMBS UP (All 4 4-finger curl state)
        # -------------------------------------------------------------
        if all_curled:
            # Thumb must point vertically upward (tip above IP, IP above MCP, tip well above index knuckle)
            d_thumb_len = np.linalg.norm(thumb_tip - thumb_mcp)
            d_thumb_segments = np.linalg.norm(thumb_tip - thumb_ip) + np.linalg.norm(thumb_ip - thumb_mcp)
            thumb_curl = 1.0 - (d_thumb_len / max(1e-4, d_thumb_segments))

            is_thumb_up = (
                (thumb_tip[1] < index_mcp[1] - 0.08 * scale_factor) and
                (thumb_tip[1] < thumb_mcp[1] - 0.06 * scale_factor) and
                (thumb_curl < 0.25)
            )

            if is_thumb_up:
                token = GestureToken.THUMBS_UP
                c_conf = float(sigmoid(index_mcp[1] - thumb_tip[1], steepness=20.0 / scale_factor, midpoint=0.08))
                c_conf = max(0.75, c_conf)
            else:
                token = GestureToken.FIST
                mean_curl = float(np.mean([curls[f] for f in ["index", "middle", "ring", "pinky"]]))
                c_conf = float(sigmoid(mean_curl, steepness=20.0, midpoint=self.fist_curl_threshold))
                c_conf = max(0.80, c_conf)

            self._update_stable_duration(token, delta_t)
            token_def = self.vocabulary.get_definition(token)
            return GestureClassification(
                gesture_token=token,
                c_gesture=c_conf,
                requires_gaze_target=token_def.requires_gaze_target,
                action_intent=token_def.mapped_action.value if not token_def.is_rest_state else "NO_ACTION",
                stable_duration_ms=self._stable_duration_ms,
                timestamp_ms=timestamp_ms
            )

        # -------------------------------------------------------------
        # 2. PINCH FAMILY EVALUATION (Thumb to Fingertip Contact)
        # -------------------------------------------------------------
        pinch_distances = {
            GestureToken.PINCH_INDEX: float(np.linalg.norm(thumb_tip - index_tip)),
            GestureToken.PINCH_MIDDLE: float(np.linalg.norm(thumb_tip - middle_tip)),
            GestureToken.PINCH_RING: float(np.linalg.norm(thumb_tip - ring_tip)),
            GestureToken.PINCH_PINKY: float(np.linalg.norm(thumb_tip - pinky_tip)),
        }

        best_pinch_token, min_dist = min(pinch_distances.items(), key=lambda x: x[1])
        base_thresh = self.default_pinch_threshold * scale_factor
        if personalized_thresholds and best_pinch_token.value in personalized_thresholds:
            base_thresh = personalized_thresholds[best_pinch_token.value] * scale_factor

        effective_pinch_thresh = max(0.05, base_thresh)

        if min_dist <= effective_pinch_thresh:
            c_conf = float(sigmoid(effective_pinch_thresh - min_dist, steepness=35.0 / scale_factor, midpoint=0.0))
            c_conf = max(0.70, c_conf)

            if (self._current_token == best_pinch_token or self._current_token == GestureToken.PINCH_HOLD) and \
               self._stable_duration_ms >= self.pinch_hold_duration_ms:
                active_token = GestureToken.PINCH_HOLD
            else:
                active_token = best_pinch_token

            self._update_stable_duration(active_token, delta_t)
            token_def = self.vocabulary.get_definition(active_token)
            return GestureClassification(
                gesture_token=active_token,
                c_gesture=c_conf,
                requires_gaze_target=token_def.requires_gaze_target,
                action_intent=token_def.mapped_action.value,
                stable_duration_ms=self._stable_duration_ms,
                timestamp_ms=timestamp_ms
            )

        # -------------------------------------------------------------
        # 3. OPEN PALM EVALUATION (All Fingers Extended)
        # -------------------------------------------------------------
        all_extended = all(curls[f] <= 0.48 for f in ["index", "middle", "ring", "pinky"])
        if all_extended and min_dist > 0.12 * scale_factor:
            token = GestureToken.OPEN_PALM
            c_conf = 0.85
            self._update_stable_duration(token, delta_t)
            token_def = self.vocabulary.get_definition(token)
            return GestureClassification(
                gesture_token=token,
                c_gesture=c_conf,
                requires_gaze_target=token_def.requires_gaze_target,
                action_intent=token_def.mapped_action.value,
                stable_duration_ms=self._stable_duration_ms,
                timestamp_ms=timestamp_ms
            )

        # -------------------------------------------------------------
        # 4. DYNAMIC SWIPE GESTURES
        # -------------------------------------------------------------
        if hand.wrist_velocity >= 2.0:
            current_wrist = (pts[self.WRIST][0], pts[self.WRIST][1], pts[self.WRIST][2])
            if self._prev_wrist_pos is not None:
                dx = current_wrist[0] - self._prev_wrist_pos[0]
                dy = current_wrist[1] - self._prev_wrist_pos[1]
                abs_dx = abs(dx)
                abs_dy = abs(dy)

                if abs_dx > abs_dy and abs_dx > 0.02:
                    token = GestureToken.SWIPE_LEFT if dx < 0 else GestureToken.SWIPE_RIGHT
                elif abs_dy > abs_dx and abs_dy > 0.02:
                    token = GestureToken.SWIPE_UP if dy < 0 else GestureToken.SWIPE_DOWN
                else:
                    token = GestureToken.NONE

                if token != GestureToken.NONE:
                    c_conf = float(sigmoid(hand.wrist_velocity, steepness=2.0, midpoint=2.0))
                    self._update_stable_duration(token, delta_t)
                    self._prev_wrist_pos = current_wrist
                    token_def = self.vocabulary.get_definition(token)
                    return GestureClassification(
                        gesture_token=token,
                        c_gesture=c_conf,
                        requires_gaze_target=token_def.requires_gaze_target,
                        action_intent=token_def.mapped_action.value,
                        stable_duration_ms=self._stable_duration_ms,
                        timestamp_ms=timestamp_ms
                    )

            self._prev_wrist_pos = current_wrist
        else:
            self._prev_wrist_pos = (pts[self.WRIST][0], pts[self.WRIST][1], pts[self.WRIST][2])

        # -------------------------------------------------------------
        # 5. DEFAULT FALLBACK
        # -------------------------------------------------------------
        self._update_stable_duration(GestureToken.NONE, delta_t)
        return GestureClassification(
            gesture_token=GestureToken.NONE,
            c_gesture=0.0,
            requires_gaze_target=False,
            action_intent="NO_ACTION",
            stable_duration_ms=self._stable_duration_ms,
            timestamp_ms=timestamp_ms
        )

    def _update_stable_duration(self, token: GestureToken, delta_t_ms: float) -> None:
        """Updates stability timer based on whether the token is maintained across frames."""
        if token == self._current_token and token != GestureToken.NONE:
            self._stable_duration_ms += delta_t_ms
        else:
            self._current_token = token
            self._stable_duration_ms = 0.0

    def _compute_finger_curls(self, pts: np.ndarray) -> Dict[str, float]:
        """Calculates normalized finger curl ratios."""
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


__all__ = ["GestureClassifier"]
