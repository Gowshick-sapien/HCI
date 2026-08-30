"""
Engine 5B: Gatekeeper SPRT Statistical Validator.
Applies Sequential Probability Ratio Test (SPRT) to validate online parameter adaptation candidates.
"""

from __future__ import annotations

import logging
import math
import threading
from typing import List, Optional
import numpy as np

from src.storage.schemas import (
    FeedbackEvent,
    FeedbackType,
    GatekeeperDecision,
    GatekeeperVerdict,
)

logger = logging.getLogger(__name__)


class Gatekeeper:
    """
    Statistical hypothesis testing gatekeeper.
    Employs Wald's Sequential Probability Ratio Test (SPRT) to filter spurious feedback
    and confirm genuine systematic interaction drift before approving online micro-SGD updates.
    """

    def __init__(
        self,
        alpha_type1: float = 0.05,
        beta_type2: float = 0.10,
        p0_noise: float = 0.10,
        p1_bias: float = 0.60,
        min_samples: int = 3,
        min_confidence_threshold: float = 0.65,
        learning_rate_base: float = 0.04
    ) -> None:
        self.alpha_type1 = float(alpha_type1)
        self.beta_type2 = float(beta_type2)
        self.p0_noise = float(p0_noise)
        self.p1_bias = float(p1_bias)
        self.min_samples = int(min_samples)
        self.min_confidence_threshold = float(min_confidence_threshold)
        self.learning_rate_base = float(learning_rate_base)

        # SPRT Decision Thresholds
        self.threshold_upper_A = math.log((1.0 - self.beta_type2) / self.alpha_type1) # ~2.890
        self.threshold_lower_B = math.log(self.beta_type2 / (1.0 - self.alpha_type1)) # ~-2.251

        # Increments
        self._ll_error = math.log(self.p1_bias / self.p0_noise)
        self._ll_success = math.log((1.0 - self.p1_bias) / (1.0 - self.p0_noise))

        self._lock = threading.RLock()
        self._sprt_score: float = 0.0
        self._accumulated_samples: int = 0
        self._recent_events: List[FeedbackEvent] = []

    def evaluate_feedback(self, feedback: FeedbackEvent) -> GatekeeperDecision:
        """
        Ingests a FeedbackEvent, updates the SPRT cumulative log-likelihood, and returns a GatekeeperDecision.
        """
        is_error = (feedback.feedback_type == FeedbackType.IMPLICIT_NEG)
        conf = float(np.clip(feedback.confidence_cfb, 0.1, 1.0))

        # Confidence weighting
        increment = (self._ll_error if is_error else self._ll_success) * conf

        with self._lock:
            self._sprt_score += increment
            self._accumulated_samples += 1
            self._recent_events.append(feedback)

            # Check rejection conditions
            if conf < self.min_confidence_threshold:
                return GatekeeperDecision(
                    verdict=GatekeeperVerdict.REJECT,
                    rejection_reason=f"Confidence {conf:.2f} < threshold {self.min_confidence_threshold:.2f}",
                    sample_count=self._accumulated_samples,
                    confidence_cfb=conf,
                    sprt_score=float(self._sprt_score),
                    effective_learning_rate_scale=0.0
                )

            if self._accumulated_samples < self.min_samples and is_error:
                # Need minimum evidence before triggering update
                return GatekeeperDecision(
                    verdict=GatekeeperVerdict.REJECT,
                    rejection_reason=f"Sample count {self._accumulated_samples} < min required {self.min_samples}",
                    sample_count=self._accumulated_samples,
                    confidence_cfb=conf,
                    sprt_score=float(self._sprt_score),
                    effective_learning_rate_scale=0.0
                )

            # Check SPRT Lower Boundary (H0 confirmed: Random noise -> Reset and REJECT)
            if self._sprt_score <= self.threshold_lower_B:
                reason = f"SPRT score {self._sprt_score:.2f} <= lower bound B ({self.threshold_lower_B:.2f})"
                self._sprt_score = 0.0
                self._accumulated_samples = 0
                return GatekeeperDecision(
                    verdict=GatekeeperVerdict.REJECT,
                    rejection_reason=reason,
                    sample_count=self._accumulated_samples,
                    confidence_cfb=conf,
                    sprt_score=float(self._sprt_score),
                    effective_learning_rate_scale=0.0
                )

            # Check SPRT Upper Boundary (H1 confirmed: Systematic drift -> APPROVE)
            if self._sprt_score >= self.threshold_upper_A or (is_error and self._accumulated_samples >= self.min_samples and self._sprt_score > 1.5):
                # Scale learning rate by confidence and severity
                sev_multiplier = 1.0 + (feedback.severity - 1) * 0.25
                lr_scale = float(np.clip(conf * sev_multiplier, 0.2, 2.0))

                # Reset SPRT accumulator post-approval to begin fresh monitoring
                self._sprt_score = 0.0
                self._accumulated_samples = 0

                return GatekeeperDecision(
                    verdict=GatekeeperVerdict.APPROVE,
                    rejection_reason=None,
                    sample_count=self._accumulated_samples,
                    confidence_cfb=conf,
                    sprt_score=float(self._sprt_score),
                    effective_learning_rate_scale=lr_scale
                )

            # Intermediate region (Indeterminate -> REJECT update pending further evidence)
            return GatekeeperDecision(
                verdict=GatekeeperVerdict.REJECT,
                rejection_reason=f"SPRT score {self._sprt_score:.2f} in indeterminate region ({self.threshold_lower_B:.2f}, {self.threshold_upper_A:.2f})",
                sample_count=self._accumulated_samples,
                confidence_cfb=conf,
                sprt_score=float(self._sprt_score),
                effective_learning_rate_scale=0.0
            )

    def reset(self) -> None:
        """Resets SPRT accumulators."""
        with self._lock:
            self._sprt_score = 0.0
            self._accumulated_samples = 0
            self._recent_events.clear()


__all__ = ["Gatekeeper"]
