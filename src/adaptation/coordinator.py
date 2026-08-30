"""
Master Layer 5 Coordinator: Dual-Scale Dynamic Adaptation & Runtime Assessment.
Orchestrates Engine 5A (Assessment), Engine 5B (Gatekeeper & Micro-SGD),
and Engine 5C (Macro-Adaptation) with persistent profile management.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Dict, List, Optional, Tuple
import numpy as np

from src.adaptation.assessment_engine import AssessmentEngine
from src.adaptation.gatekeeper import Gatekeeper
from src.adaptation.macro_adaptation import MacroAdaptationEngine
from src.adaptation.micro_adaptation import MicroAdaptationEngine
from src.storage.profile_manager import ProfileManager
from src.storage.schemas import (
    AssessmentMetrics,
    FeedbackEvent,
    GatekeeperDecision,
    GatekeeperVerdict,
    MacroPolicy,
    ProfileSnapshot,
    SystemHealthState,
)

logger = logging.getLogger(__name__)


class AdaptationCoordinator:
    """
    Unified coordinator facade for Layer 5 Dual-Scale Dynamic Adaptation.
    Subscribes to Layer 4 supervisory feedback and maintains closed-loop convergence.
    """

    def __init__(
        self,
        assessment_engine: Optional[AssessmentEngine] = None,
        gatekeeper: Optional[Gatekeeper] = None,
        micro_adaptation: Optional[MicroAdaptationEngine] = None,
        macro_adaptation: Optional[MacroAdaptationEngine] = None,
        profile_manager: Optional[ProfileManager] = None,
        user_id: str = "default_user"
    ) -> None:
        self.user_id = user_id
        self.assessment_engine = assessment_engine or AssessmentEngine()
        self.gatekeeper = gatekeeper or Gatekeeper()
        self.micro_adaptation = micro_adaptation or MicroAdaptationEngine()
        self.macro_adaptation = macro_adaptation or MacroAdaptationEngine()
        self.profile_manager = profile_manager or ProfileManager()

        self._lock = threading.RLock()
        self._active_profile: ProfileSnapshot = self.profile_manager.load_profile(self.user_id)
        self.micro_adaptation.set_weights_from_profile(self._active_profile)

        self._latest_metrics: AssessmentMetrics = self.assessment_engine.compute_metrics()
        self._latest_decision: Optional[GatekeeperDecision] = None
        self._latest_policy: MacroPolicy = MacroPolicy.MERGE

    @property
    def current_profile(self) -> ProfileSnapshot:
        with self._lock:
            return self._active_profile

    def get_active_weights(self) -> Dict[str, float]:
        """Returns the current runtime modality weights dictionary."""
        return self.micro_adaptation.current_weights_dict

    def get_latest_metrics(self) -> AssessmentMetrics:
        """Returns the latest runtime assessment health metrics."""
        with self._lock:
            return self._latest_metrics

    def process_feedback_event(
        self,
        feedback: FeedbackEvent,
        weights_snapshot: Optional[Dict[str, float]] = None,
        ambient_lux: float = 50.0,
        current_time: Optional[float] = None
    ) -> Tuple[AssessmentMetrics, GatekeeperDecision, MacroPolicy, Dict[str, float]]:
        """
        Executes complete closed-loop adaptation cycle for an incoming FeedbackEvent.

        Returns:
            Tuple of (AssessmentMetrics, GatekeeperDecision, MacroPolicy, active_weights_dict).
        """
        now = current_time if current_time is not None else time.time()

        with self._lock:
            current_w = weights_snapshot or self.get_active_weights()

            # 1. Engine 5A: Update runtime performance metrics
            self._latest_metrics = self.assessment_engine.record_interaction(
                feedback=feedback,
                weights_snapshot=current_w,
                interaction_confidence=feedback.confidence_cfb,
                timestamp=now
            )

            # 2. Engine 5C: Evaluate Macro-Adaptation Policy
            self._latest_policy = self.macro_adaptation.evaluate_policy(
                metrics=self._latest_metrics,
                ambient_lux=ambient_lux,
                current_time=now
            )

            # 3. Policy Execution & Engine 5B Micro-Adaptation
            if self._latest_policy == MacroPolicy.DISCARD:
                # Rollback tentative session weights to permanent baseline
                restored_w = self.micro_adaptation.reset_to_baseline()
                self._latest_decision = GatekeeperDecision(
                    verdict=GatekeeperVerdict.REJECT,
                    rejection_reason="Macro-policy DISCARD rollback triggered",
                    sample_count=0,
                    confidence_cfb=feedback.confidence_cfb,
                    sprt_score=0.0,
                    effective_learning_rate_scale=0.0
                )
                logger.warning(f"AdaptationCoordinator DISCARD rollback executed for user '{self.user_id}'")
                return self._latest_metrics, self._latest_decision, self._latest_policy, restored_w

            if self._latest_policy == MacroPolicy.FREEZE:
                # Freeze online learning
                self._latest_decision = GatekeeperDecision(
                    verdict=GatekeeperVerdict.REJECT,
                    rejection_reason="Macro-policy FREEZE active (high noise or drifting)",
                    sample_count=0,
                    confidence_cfb=feedback.confidence_cfb,
                    sprt_score=0.0,
                    effective_learning_rate_scale=0.0
                )
                return self._latest_metrics, self._latest_decision, self._latest_policy, self.get_active_weights()

            # 4. Engine 5B: SPRT Gatekeeper Evaluation
            self._latest_decision = self.gatekeeper.evaluate_feedback(feedback)

            # 5. Engine 5B: Micro-SGD Gradient Descent
            updated_w, was_updated = self.micro_adaptation.adapt(feedback, self._latest_decision)

            # 6. Apply MERGE when sustained convergence achieved
            if was_updated and self._latest_policy == MacroPolicy.MERGE and self._latest_metrics.health_state == SystemHealthState.STABLE:
                merged_w = self.macro_adaptation.execute_merge(
                    baseline_weights=self._active_profile.modality_weights,
                    session_weights=updated_w
                )
                # Update persistent profile state
                self._active_profile.version_id += 1
                self._active_profile.timestamp_epoch = now
                self._active_profile.modality_weights = merged_w
                self._active_profile.adaptation_confidence_index = self._latest_metrics.adaptation_confidence_index
                self._active_profile.weight_stability_index = self._latest_metrics.weight_stability_index
                self._active_profile.expected_calibration_error = self._latest_metrics.expected_calibration_error
                self._active_profile.cumulative_adaptation_gain = self._latest_metrics.adaptation_gain_ewma
                self._active_profile.total_interactions_seen = self._latest_metrics.interactions_count
                self._active_profile.total_updates_approved += 1

                self.profile_manager.save_profile(self._active_profile)

            return self._latest_metrics, self._latest_decision, self._latest_policy, self.get_active_weights()

    def reset(self) -> None:
        """Resets coordinator and sub-engines."""
        with self._lock:
            self.assessment_engine.reset()
            self.gatekeeper.reset()
            self.macro_adaptation.reset()
            self._active_profile = self.profile_manager.load_profile(self.user_id)
            self.micro_adaptation.set_weights_from_profile(self._active_profile)
            self._latest_metrics = self.assessment_engine.compute_metrics()
            self._latest_decision = None
            self._latest_policy = MacroPolicy.MERGE


__all__ = ["AdaptationCoordinator"]
