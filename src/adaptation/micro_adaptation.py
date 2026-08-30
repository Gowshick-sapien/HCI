"""
Engine 5B: Online Micro-Adaptation Engine.
Executes feedback-driven gradient descent on modality weights with probability simplex projection.
"""

from __future__ import annotations

import logging
import threading
from typing import Dict, List, Optional, Tuple
import numpy as np

from src.storage.schemas import (
    FailureMode,
    FeedbackEvent,
    FeedbackType,
    GatekeeperDecision,
    GatekeeperVerdict,
    ProfileSnapshot,
)

logger = logging.getLogger(__name__)


def project_to_simplex_with_min(v: np.ndarray, min_weight: float = 0.05) -> np.ndarray:
    """
    Projects a vector v onto the probability simplex with a minimum component bound:
    sum(w) = 1.0, w_i >= min_weight > 0.
    """
    n = len(v)
    v_clean = np.array(v, dtype=np.float64)

    # Shift by min_weight
    remaining_mass = 1.0 - (n * min_weight)
    if remaining_mass <= 0.0:
        return np.full(n, 1.0 / n, dtype=np.float64)

    # Standard Euclidean projection onto simplex of mass 'remaining_mass'
    u = np.sort(v_clean - min_weight)[::-1]
    cssv = np.cumsum(u)
    rho_indices = np.nonzero(u * np.arange(1, n + 1) > (cssv - remaining_mass))[0]

    if len(rho_indices) == 0:
        theta = (np.sum(v_clean - min_weight) - remaining_mass) / n
    else:
        rho = rho_indices[-1]
        theta = (cssv[rho] - remaining_mass) / float(rho + 1)

    w = np.maximum(v_clean - min_weight - theta, 0.0) + min_weight
    # Re-normalize to guarantee exact sum = 1.0
    return w / np.sum(w)


class MicroAdaptationEngine:
    """
    Engine 5B: Online gradient descent optimizer for multimodal fusion weights.
    Adjusts weights [w_eye, w_head, w_hand] based on supervisory feedback and Gatekeeper approval.
    """

    def __init__(
        self,
        base_learning_rate: float = 0.035,
        min_modality_weight: float = 0.05,
        max_step_bound: float = 0.08,
        regularization_lambda: float = 0.02
    ) -> None:
        self.base_learning_rate = float(base_learning_rate)
        self.min_modality_weight = float(min_modality_weight)
        self.max_step_bound = float(max_step_bound)
        self.regularization_lambda = float(regularization_lambda)

        self._lock = threading.RLock()
        self._current_weights: np.ndarray = np.array([0.40, 0.30, 0.30], dtype=np.float64) # [EYE, HEAD, HAND]
        self._baseline_weights: np.ndarray = np.array([0.40, 0.30, 0.30], dtype=np.float64)

    def set_weights_from_profile(self, profile: ProfileSnapshot) -> None:
        """Initializes weights from an existing profile snapshot."""
        with self._lock:
            w_eye = profile.modality_weights.get("EYE", profile.modality_weights.get("GAZE", 0.40))
            w_head = profile.modality_weights.get("HEAD", 0.30)
            w_hand = profile.modality_weights.get("HAND", profile.modality_weights.get("GESTURE", 0.30))
            w_arr = np.array([w_eye, w_head, w_hand], dtype=np.float64)
            w_arr = project_to_simplex_with_min(w_arr, self.min_modality_weight)
            self._current_weights = w_arr
            self._baseline_weights = w_arr.copy()

    @property
    def current_weights_dict(self) -> Dict[str, float]:
        with self._lock:
            return {
                "EYE": float(self._current_weights[0]),
                "HEAD": float(self._current_weights[1]),
                "HAND": float(self._current_weights[2]),
                "GAZE": float(self._current_weights[0]),
                "GESTURE": float(self._current_weights[2])
            }

    def adapt(
        self,
        feedback: FeedbackEvent,
        gatekeeper_decision: GatekeeperDecision
    ) -> Tuple[Dict[str, float], bool]:
        """
        Applies an online micro-SGD adaptation step if Gatekeeper approved the update.

        Returns:
            Tuple of (updated_weights_dict, was_updated_bool).
        """
        if gatekeeper_decision.verdict != GatekeeperVerdict.APPROVE:
            return self.current_weights_dict, False

        with self._lock:
            eta = self.base_learning_rate * gatekeeper_decision.effective_learning_rate_scale

            # Compute failure-mode specific loss gradient: \nabla_w L
            grad = self._compute_feedback_gradient(feedback)

            # Add L2 baseline regularization gradient: lambda * (w - w_base)
            reg_grad = self.regularization_lambda * (self._current_weights - self._baseline_weights)
            total_grad = grad + reg_grad

            # Raw gradient descent step
            delta_w = -eta * total_grad

            # Clip max step bound
            delta_w = np.clip(delta_w, -self.max_step_bound, self.max_step_bound)

            # Candidate weights
            w_candidate = self._current_weights + delta_w

            # Project to probability simplex with minimum bound
            w_projected = project_to_simplex_with_min(w_candidate, self.min_modality_weight)

            # Apply update
            self._current_weights = w_projected
            logger.info(f"MicroAdaptation updated weights: EYE={w_projected[0]:.3f}, HEAD={w_projected[1]:.3f}, HAND={w_projected[2]:.3f}")

            return self.current_weights_dict, True

    def _compute_feedback_gradient(self, feedback: FeedbackEvent) -> np.ndarray:
        """
        Computes analytical loss gradient vector [grad_eye, grad_head, grad_hand] based on failure mode.
        """
        # [EYE, HEAD, HAND]
        if feedback.feedback_type == FeedbackType.IMPLICIT_POS:
            # Positive confirmation: reward current distribution
            return -0.20 * self._current_weights

        mode = feedback.failure_mode

        if mode == FailureMode.WRONG_TARGET:
            # Gaze/Eye was pointing at wrong target: heavily penalize eye, shift to head & hand
            return np.array([1.2, -0.6, -0.6], dtype=np.float64)

        elif mode == FailureMode.USER_OVERRIDE:
            # Mouse takeover: gesture/hand triggered incorrectly, penalize hand and eye
            return np.array([0.4, -0.8, 0.4], dtype=np.float64)

        elif mode == FailureMode.FALSE_ACTIVATION:
            # Spurious activation: penalize hand gesture trigger
            return np.array([-0.5, -0.5, 1.0], dtype=np.float64)

        elif mode == FailureMode.DELAYED_RESPONSE or mode == FailureMode.LOW_CONFIDENCE:
            # Boost fastest available modality
            return np.array([-0.4, 0.2, 0.2], dtype=np.float64)

        # Generic default penalty on highest weight
        grad = np.zeros(3, dtype=np.float64)
        max_idx = np.argmax(self._current_weights)
        grad[max_idx] = 0.8
        for i in range(3):
            if i != max_idx:
                grad[i] = -0.4
        return grad

    def reset_to_baseline(self) -> Dict[str, float]:
        """Restores weights to baseline profile state."""
        with self._lock:
            self._current_weights = self._baseline_weights.copy()
            return self.current_weights_dict


__all__ = ["MicroAdaptationEngine", "project_to_simplex_with_min"]
