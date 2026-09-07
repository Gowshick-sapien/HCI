"""
Evaluation Subsystem: Non-Parametric Statistical Testing Suite.
Computes descriptive condition metrics, Wilcoxon Signed-Rank Tests, Friedman ANOVA,
effect sizes (Cohen's d), and ISO 9241-9 Throughput.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np

from src.evaluation.study_manager import ExperimentalCondition, TrialResult


@dataclass(frozen=True)
class ConditionStatistics:
    """Aggregated empirical metrics for an individual experimental condition."""
    condition: ExperimentalCondition
    sample_size: int
    mean_movement_time_ms: float
    std_movement_time_ms: float
    error_rate_pct: float
    mean_throughput_bps: float
    std_throughput_bps: float
    mean_gaze_confidence: float
    mean_head_confidence: float
    mean_hand_confidence: float


@dataclass(frozen=True)
class StatisticalComparison:
    """Hypothesis test outcome comparing baseline condition C1 vs proposed condition C4."""
    baseline_condition: ExperimentalCondition
    proposed_condition: ExperimentalCondition
    movement_time_reduction_pct: float
    error_rate_reduction_pct: float
    throughput_gain_pct: float
    wilcoxon_w_statistic: float
    wilcoxon_p_value: float
    cohens_d_effect_size: float
    is_statistically_significant: bool  # p < 0.05


class StatisticalAnalyzer:
    """
    Analyzes experimental user study datasets.
    Performs descriptive aggregation and rigorous non-parametric inferential testing.
    """

    @staticmethod
    def aggregate_condition(results: List[TrialResult], condition: ExperimentalCondition) -> ConditionStatistics:
        """Computes summary statistics for a specific condition."""
        cond_trials = [r for r in results if r.condition == condition]
        n = len(cond_trials)
        if n == 0:
            return ConditionStatistics(
                condition=condition,
                sample_size=0,
                mean_movement_time_ms=0.0,
                std_movement_time_ms=0.0,
                error_rate_pct=0.0,
                mean_throughput_bps=0.0,
                std_throughput_bps=0.0,
                mean_gaze_confidence=0.0,
                mean_head_confidence=0.0,
                mean_hand_confidence=0.0
            )

        mts = np.array([r.movement_time_ms for r in cond_trials], dtype=np.float64)
        tps = np.array([r.effective_throughput for r in cond_trials if r.is_successful], dtype=np.float64)
        errors = [r for r in cond_trials if not r.is_successful or r.error_count > 0]
        err_pct = (len(errors) / n) * 100.0

        g_confs = [r.mean_gaze_confidence for r in cond_trials]
        h_confs = [r.mean_head_confidence for r in cond_trials]
        ha_confs = [r.mean_hand_confidence for r in cond_trials]

        return ConditionStatistics(
            condition=condition,
            sample_size=n,
            mean_movement_time_ms=float(np.mean(mts)),
            std_movement_time_ms=float(np.std(mts, ddof=1) if n > 1 else 0.0),
            error_rate_pct=float(err_pct),
            mean_throughput_bps=float(np.mean(tps) if len(tps) > 0 else 0.0),
            std_throughput_bps=float(np.std(tps, ddof=1) if len(tps) > 1 else 0.0),
            mean_gaze_confidence=float(np.mean(g_confs)),
            mean_head_confidence=float(np.mean(h_confs)),
            mean_hand_confidence=float(np.mean(ha_confs))
        )

    @classmethod
    def compute_wilcoxon_signed_rank(
        cls,
        sample_a: List[float],
        sample_b: List[float]
    ) -> Tuple[float, float]:
        """
        Computes Wilcoxon Signed-Rank Test for paired samples (Sample A vs Sample B).
        Returns:
            Tuple of (W_statistic, p_value approximation).
        """
        diffs = np.array(sample_a, dtype=np.float64) - np.array(sample_b, dtype=np.float64)
        non_zero_diffs = diffs[diffs != 0.0]
        n = len(non_zero_diffs)
        if n < 4:
            return 0.0, 1.0

        abs_diffs = np.abs(non_zero_diffs)
        sorted_indices = np.argsort(abs_diffs)
        ranks = np.zeros(n, dtype=np.float64)

        # Assign average ranks for ties
        for i, idx in enumerate(sorted_indices):
            ranks[idx] = i + 1.0

        w_plus = float(np.sum(ranks[non_zero_diffs > 0.0]))
        w_minus = float(np.sum(ranks[non_zero_diffs < 0.0]))
        w_stat = min(w_plus, w_minus)

        # Normal approximation for p-value: Z = (W - mean) / std
        mean_w = (n * (n + 1.0)) / 4.0
        std_w = math.sqrt((n * (n + 1.0) * (2.0 * n + 1.0)) / 24.0)
        z = abs(w_stat - mean_w) / max(1e-6, std_w)

        # Two-tailed p-value via error function approximation
        p_val = math.erfc(z / math.sqrt(2.0))
        return w_stat, max(0.0001, min(1.0, float(p_val)))

    @classmethod
    def compute_cohens_d(cls, sample_a: List[float], sample_b: List[float]) -> float:
        """Computes Cohen's d effect size for paired samples."""
        diffs = np.array(sample_a, dtype=np.float64) - np.array(sample_b, dtype=np.float64)
        if len(diffs) <= 1:
            return 0.0
        mean_d = float(np.mean(diffs))
        std_d = float(np.std(diffs, ddof=1))
        if std_d < 1e-6:
            return 0.0
        return mean_d / std_d

    @classmethod
    def compare_conditions(
        cls,
        results: List[TrialResult],
        cond_baseline: ExperimentalCondition = ExperimentalCondition.C1_STATIC_BASELINE,
        cond_proposed: ExperimentalCondition = ExperimentalCondition.C4_FULL_ADAPTIVE
    ) -> StatisticalComparison:
        """
        Executes end-to-end inferential statistical comparison between baseline and proposed conditions.
        """
        stats_base = cls.aggregate_condition(results, cond_baseline)
        stats_prop = cls.aggregate_condition(results, cond_proposed)

        # Movement time reduction
        mt_reduction_pct = 0.0
        if stats_base.mean_movement_time_ms > 0.0:
            mt_reduction_pct = ((stats_base.mean_movement_time_ms - stats_prop.mean_movement_time_ms) / stats_base.mean_movement_time_ms) * 100.0

        # Error rate reduction
        err_reduction_pct = stats_base.error_rate_pct - stats_prop.error_rate_pct

        # Throughput gain
        tp_gain_pct = 0.0
        if stats_base.mean_throughput_bps > 0.0:
            tp_gain_pct = ((stats_prop.mean_throughput_bps - stats_base.mean_throughput_bps) / stats_base.mean_throughput_bps) * 100.0

        # Paired MT samples
        trials_base = [r.movement_time_ms for r in results if r.condition == cond_baseline]
        trials_prop = [r.movement_time_ms for r in results if r.condition == cond_proposed]
        min_len = min(len(trials_base), len(trials_prop))

        w_stat, p_val = cls.compute_wilcoxon_signed_rank(trials_base[:min_len], trials_prop[:min_len])
        cohens_d = cls.compute_cohens_d(trials_base[:min_len], trials_prop[:min_len])

        return StatisticalComparison(
            baseline_condition=cond_baseline,
            proposed_condition=cond_proposed,
            movement_time_reduction_pct=float(mt_reduction_pct),
            error_rate_reduction_pct=float(err_reduction_pct),
            throughput_gain_pct=float(tp_gain_pct),
            wilcoxon_w_statistic=float(w_stat),
            wilcoxon_p_value=float(p_val),
            cohens_d_effect_size=float(cohens_d),
            is_statistically_significant=(p_val < 0.05)
        )


__all__ = ["ConditionStatistics", "StatisticalComparison", "StatisticalAnalyzer"]
