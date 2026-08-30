"""
Engine 5A: Runtime Performance Assessment Engine.
Computes statistical health, stability, and calibration metrics over sliding interaction windows.
"""

from __future__ import annotations

import collections
import logging
import threading
import time
from typing import Deque, Dict, List, Optional, Tuple
import numpy as np

from src.storage.schemas import (
    AssessmentMetrics,
    FeedbackEvent,
    FeedbackType,
    SystemHealthState,
)

logger = logging.getLogger(__name__)


class AssessmentEngine:
    """
    Engine 5A: Real-time statistical performance evaluator.
    Tracks adaptation gain, learning velocity, weight stability index, ECE,
    and classifies system health state.
    """

    def __init__(
        self,
        window_size: int = 30,
        gain_alpha: float = 0.15,
        stability_var_threshold: float = 0.04,
        drift_ece_threshold: float = 0.15,
        min_bootstrap_samples: int = 8
    ) -> None:
        self.window_size = int(window_size)
        self.gain_alpha = float(gain_alpha)
        self.stability_var_threshold = float(stability_var_threshold)
        self.drift_ece_threshold = float(drift_ece_threshold)
        self.min_bootstrap_samples = int(min_bootstrap_samples)

        self._lock = threading.RLock()

        # Rolling history buffers: (timestamp, success_bool, confidence, weights_array)
        self._history: Deque[Tuple[float, bool, float, np.ndarray]] = collections.deque(maxlen=self.window_size)
        self._interaction_count: int = 0

        # Performance states
        self._ewma_gain: float = 0.0
        self._last_accuracy: float = 0.85
        self._drift_start_timestamp: Optional[float] = None
        self._drift_recovery_times: List[float] = []

    def record_interaction(
        self,
        feedback: FeedbackEvent,
        weights_snapshot: Optional[Dict[str, float]] = None,
        interaction_confidence: float = 0.80,
        timestamp: Optional[float] = None
    ) -> AssessmentMetrics:
        """
        Ingests a FeedbackEvent, updates performance metrics, and returns a new AssessmentMetrics snapshot.
        """
        now = timestamp if timestamp is not None else time.time()
        is_success = (feedback.feedback_type == FeedbackType.IMPLICIT_POS)

        # Extract weights array [eye, head, hand]
        if weights_snapshot:
            w_arr = np.array([
                weights_snapshot.get("EYE", weights_snapshot.get("GAZE", 0.40)),
                weights_snapshot.get("HEAD", 0.30),
                weights_snapshot.get("HAND", weights_snapshot.get("GESTURE", 0.30))
            ], dtype=np.float64)
            s = np.sum(w_arr)
            if s > 0:
                w_arr /= s
        else:
            w_arr = np.array([0.40, 0.30, 0.30], dtype=np.float64)

        with self._lock:
            self._interaction_count += 1
            self._history.append((now, is_success, float(interaction_confidence), w_arr))
            return self.compute_metrics(current_time=now)

    def compute_metrics(self, current_time: Optional[float] = None) -> AssessmentMetrics:
        """
        Computes real-time assessment metrics from the rolling interaction window.
        """
        now = current_time if current_time is not None else time.time()

        with self._lock:
            n_samples = len(self._history)
            if n_samples == 0:
                return AssessmentMetrics(
                    timestamp=now,
                    interactions_count=0,
                    adaptation_gain_ewma=0.0,
                    learning_velocity=0.0,
                    weight_stability_index=1.0,
                    adaptation_confidence_index=0.50,
                    expected_calibration_error=0.0,
                    recovery_rate=1.0,
                    drift_recovery_time=0.0,
                    health_state=SystemHealthState.BOOTSTRAPPING
                )

            # 1. Current window accuracy & EWMA Adaptation Gain
            successes = [h[1] for h in self._history]
            current_acc = float(np.mean(successes))
            acc_delta = current_acc - self._last_accuracy
            self._ewma_gain = (self.gain_alpha * acc_delta) + ((1.0 - self.gain_alpha) * self._ewma_gain)
            self._last_accuracy = current_acc

            # 2. Learning Velocity: rate of weight vector change
            if n_samples >= 2:
                weights_matrix = np.array([h[3] for h in self._history]) # Shape: (N, 3)
                w_diff = weights_matrix[-1] - weights_matrix[0]
                dt = max(0.1, self._history[-1][0] - self._history[0][0])
                velocity = float(np.linalg.norm(w_diff) / dt)
            else:
                velocity = 0.0

            # 3. Weight Stability Index: 1.0 - normalized variance of weights
            if n_samples >= 3:
                weights_matrix = np.array([h[3] for h in self._history])
                var_sum = float(np.sum(np.var(weights_matrix, axis=0)))
                stability_index = float(np.clip(1.0 - (var_sum / self.stability_var_threshold), 0.0, 1.0))
            else:
                stability_index = 1.0

            # 4. Expected Calibration Error (ECE)
            ece = self._compute_ece()

            # 5. Adaptation Confidence Index
            confidences = [h[2] for h in self._history]
            mean_conf = float(np.mean(confidences))
            conf_index = float(np.clip(current_acc * (1.0 - ece), 0.0, 1.0))

            # 6. Drift Tracking & Recovery Rate (persistent severe degradation)
            is_drifting = (ece > 0.40 and current_acc < 0.40 and n_samples >= 15)

            if is_drifting:
                if self._drift_start_timestamp is None:
                    self._drift_start_timestamp = now
                recovery_time = float(now - self._drift_start_timestamp)
            else:
                if self._drift_start_timestamp is not None:
                    # Successfully recovered from drift
                    rec_t = float(now - self._drift_start_timestamp)
                    self._drift_recovery_times.append(rec_t)
                    self._drift_start_timestamp = None
                recovery_time = 0.0

            mean_rec_time = float(np.mean(self._drift_recovery_times)) if self._drift_recovery_times else 0.0
            recovery_rate = float(np.clip(1.0 / max(1.0, mean_rec_time), 0.0, 1.0)) if self._drift_recovery_times else 1.0

            # 7. System Health State Classification
            health_state = self._classify_health_state(
                n_samples=n_samples,
                current_acc=current_acc,
                velocity=velocity,
                stability=stability_index,
                is_drifting=is_drifting,
                is_recovering=(self._drift_start_timestamp is not None and self._ewma_gain > 0.0)
            )

            return AssessmentMetrics(
                timestamp=now,
                interactions_count=self._interaction_count,
                adaptation_gain_ewma=float(self._ewma_gain),
                learning_velocity=float(velocity),
                weight_stability_index=float(stability_index),
                adaptation_confidence_index=float(conf_index),
                expected_calibration_error=float(ece),
                recovery_rate=float(recovery_rate),
                drift_recovery_time=float(recovery_time),
                health_state=health_state
            )

    def _compute_ece(self, n_bins: int = 5) -> float:
        """Computes binned Expected Calibration Error."""
        if len(self._history) < 4:
            return 0.0

        confs = np.array([h[2] for h in self._history], dtype=np.float64)
        accs = np.array([1.0 if h[1] else 0.0 for h in self._history], dtype=np.float64)

        bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
        ece = 0.0
        n_total = len(confs)

        for i in range(n_bins):
            bin_lower = bin_boundaries[i]
            bin_upper = bin_boundaries[i + 1]
            in_bin = (confs >= bin_lower) & (confs < bin_upper if i < n_bins - 1 else confs <= bin_upper)
            prop_in_bin = np.sum(in_bin) / n_total

            if prop_in_bin > 0:
                bin_acc = np.mean(accs[in_bin])
                bin_conf = np.mean(confs[in_bin])
                ece += prop_in_bin * np.abs(bin_acc - bin_conf)

        return float(np.clip(ece, 0.0, 1.0))

    def _classify_health_state(
        self,
        n_samples: int,
        current_acc: float,
        velocity: float,
        stability: float,
        is_drifting: bool,
        is_recovering: bool
    ) -> SystemHealthState:
        """Classifies the holistic runtime system health state."""
        if n_samples < self.min_bootstrap_samples:
            return SystemHealthState.BOOTSTRAPPING

        if is_drifting:
            return SystemHealthState.DRIFTING

        if is_recovering:
            return SystemHealthState.RECOVERING

        if self._ewma_gain > 0.02 and current_acc >= 0.75:
            return SystemHealthState.IMPROVING

        if velocity > 0.05 and stability < 0.80:
            return SystemHealthState.LEARNING

        if stability >= 0.80 and current_acc >= 0.80:
            return SystemHealthState.STABLE

        return SystemHealthState.LEARNING

    def reset(self) -> None:
        """Resets all metrics and rolling history."""
        with self._lock:
            self._history.clear()
            self._interaction_count = 0
            self._ewma_gain = 0.0
            self._last_accuracy = 0.85
            self._drift_start_timestamp = None
            self._drift_recovery_times.clear()


__all__ = ["AssessmentEngine"]
