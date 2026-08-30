"""
Engine 5C: Macro-Adaptation Policy State Machine.
Coordinates contextual session lifecycle transitions: MERGE, FREEZE, DISCARD, and RECALIBRATE.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Dict, Optional, Tuple
import numpy as np

from src.storage.schemas import (
    AssessmentMetrics,
    MacroPolicy,
    ProfileSnapshot,
    SystemHealthState,
)

logger = logging.getLogger(__name__)


class MacroAdaptationEngine:
    """
    Engine 5C: Macro-scale adaptation policy manager.
    Governs long-term profile convergence, noise freezing, rollback safety, and calibration triggers.
    """

    def __init__(
        self,
        merge_stability_threshold: float = 0.85,
        merge_min_interactions: int = 15,
        merge_min_duration_sec: float = 45.0,
        merge_blend_factor: float = 0.50,
        discard_error_threshold: float = 0.30,
        recalibrate_ece_threshold: float = 0.28,
        min_ambient_lux_freeze: float = 15.0
    ) -> None:
        self.merge_stability_threshold = float(merge_stability_threshold)
        self.merge_min_interactions = int(merge_min_interactions)
        self.merge_min_duration_sec = float(merge_min_duration_sec)
        self.merge_blend_factor = float(merge_blend_factor)
        self.discard_error_threshold = float(discard_error_threshold)
        self.recalibrate_ece_threshold = float(recalibrate_ece_threshold)
        self.min_ambient_lux_freeze = float(min_ambient_lux_freeze)

        self._lock = threading.RLock()
        self._current_policy: MacroPolicy = MacroPolicy.MERGE
        self._stable_period_start: Optional[float] = None
        self._session_start_time: float = time.time()
        self._last_merged_timestamp: float = 0.0

    @property
    def current_policy(self) -> MacroPolicy:
        with self._lock:
            return self._current_policy

    def evaluate_policy(
        self,
        metrics: AssessmentMetrics,
        ambient_lux: float = 50.0,
        current_time: Optional[float] = None
    ) -> MacroPolicy:
        """
        Evaluates current runtime performance metrics and returns the active MacroPolicy.
        """
        now = current_time if current_time is not None else time.time()

        with self._lock:
            # 1. Check FREEZE conditions (strictly low ambient lux / darkness)
            if ambient_lux < self.min_ambient_lux_freeze:
                self._current_policy = MacroPolicy.FREEZE
                self._stable_period_start = None
                return self._current_policy

            # 2. Check RECALIBRATE conditions (severe calibration error / persistent drift)
            if metrics.expected_calibration_error >= self.recalibrate_ece_threshold and metrics.interactions_count >= self.merge_min_interactions:
                self._current_policy = MacroPolicy.RECALIBRATE
                self._stable_period_start = None
                return self._current_policy

            # 3. Check DISCARD conditions (severe instability or negative gain post-update)
            if metrics.adaptation_gain_ewma < -0.20 and metrics.weight_stability_index < 0.30:
                self._current_policy = MacroPolicy.DISCARD
                self._stable_period_start = None
                return self._current_policy

            # 4. Check MERGE conditions (sustained stability)
            if (metrics.weight_stability_index >= self.merge_stability_threshold and 
                metrics.interactions_count >= self.merge_min_interactions and
                metrics.health_state in (SystemHealthState.STABLE, SystemHealthState.IMPROVING)):
                
                if self._stable_period_start is None:
                    self._stable_period_start = now

                stable_duration = now - self._stable_period_start
                if stable_duration >= self.merge_min_duration_sec:
                    self._current_policy = MacroPolicy.MERGE
                    return self._current_policy

            else:
                self._stable_period_start = None

            self._current_policy = MacroPolicy.MERGE
            return self._current_policy

    def execute_merge(
        self,
        baseline_weights: Dict[str, float],
        session_weights: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Blends active session weights into permanent baseline profile state.
        """
        with self._lock:
            w_eye = (1.0 - self.merge_blend_factor) * baseline_weights.get("EYE", 0.4) + self.merge_blend_factor * session_weights.get("EYE", 0.4)
            w_head = (1.0 - self.merge_blend_factor) * baseline_weights.get("HEAD", 0.3) + self.merge_blend_factor * session_weights.get("HEAD", 0.3)
            w_hand = (1.0 - self.merge_blend_factor) * baseline_weights.get("HAND", 0.3) + self.merge_blend_factor * session_weights.get("HAND", 0.3)

            arr = np.array([w_eye, w_head, w_hand], dtype=np.float64)
            arr = np.maximum(arr, 0.05)
            arr /= np.sum(arr)

            self._last_merged_timestamp = time.time()
            self._stable_period_start = None
            logger.info(f"MacroAdaptation MERGED profile weights: EYE={arr[0]:.3f}, HEAD={arr[1]:.3f}, HAND={arr[2]:.3f}")

            return {
                "EYE": float(arr[0]),
                "HEAD": float(arr[1]),
                "HAND": float(arr[2]),
                "GAZE": float(arr[0]),
                "GESTURE": float(arr[2])
            }

    def reset(self) -> None:
        """Resets macro policy state."""
        with self._lock:
            self._current_policy = MacroPolicy.MERGE
            self._stable_period_start = None
            self._session_start_time = time.time()


__all__ = ["MacroAdaptationEngine"]
