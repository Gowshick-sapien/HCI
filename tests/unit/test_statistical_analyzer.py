"""
Unit tests for StatisticalAnalyzer (Deliverable E3).
Verifies Invariant INV-E3.6: Wilcoxon Signed-Rank Test, Cohen's d, and ISO 9241-9 Throughput calculation.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
from src.evaluation.statistical_analyzer import StatisticalAnalyzer
from src.evaluation.study_manager import ExperimentalCondition, TrialResult


def test_wilcoxon_signed_rank_calculation():
    """Invariant INV-E3.6: Evaluates Wilcoxon Signed-Rank test for paired samples."""
    # Sample A significantly slower than Sample B
    sample_a = [850.0, 920.0, 780.0, 890.0, 950.0, 810.0, 870.0, 900.0]
    sample_b = [520.0, 490.0, 510.0, 530.0, 540.0, 480.0, 500.0, 510.0]

    w_stat, p_val = StatisticalAnalyzer.compute_wilcoxon_signed_rank(sample_a, sample_b)
    assert w_stat >= 0.0
    assert p_val < 0.05, f"Expected significant p < 0.05, got {p_val}"

    # Effect size Cohen's d should be large (> 0.80)
    d = StatisticalAnalyzer.compute_cohens_d(sample_a, sample_b)
    assert d > 1.50


def test_condition_aggregation_and_comparison():
    """Verifies descriptive statistics aggregation and condition comparison."""
    results = []

    # Generate synthetic trials for C1 (Baseline) and C4 (Adaptive)
    for i in range(10):
        results.append(TrialResult(
            participant_id="P01",
            condition=ExperimentalCondition.C1_STATIC_BASELINE,
            block_index=0,
            trial_index=i,
            target_id=i,
            index_of_difficulty=4.5,
            movement_time_ms=800.0,
            is_successful=True,
            error_count=0,
            overshoot_count=0,
            mean_gaze_confidence=0.80,
            mean_head_confidence=0.85,
            mean_hand_confidence=0.82,
            effective_throughput=5.625
        ))
        results.append(TrialResult(
            participant_id="P01",
            condition=ExperimentalCondition.C4_FULL_ADAPTIVE,
            block_index=1,
            trial_index=i,
            target_id=i,
            index_of_difficulty=4.5,
            movement_time_ms=500.0,
            is_successful=True,
            error_count=0,
            overshoot_count=0,
            mean_gaze_confidence=0.92,
            mean_head_confidence=0.94,
            mean_hand_confidence=0.90,
            effective_throughput=9.00
        ))

    stats_c1 = StatisticalAnalyzer.aggregate_condition(results, ExperimentalCondition.C1_STATIC_BASELINE)
    stats_c4 = StatisticalAnalyzer.aggregate_condition(results, ExperimentalCondition.C4_FULL_ADAPTIVE)

    assert stats_c1.mean_movement_time_ms == 800.0
    assert stats_c4.mean_movement_time_ms == 500.0
    assert stats_c4.mean_throughput_bps > stats_c1.mean_throughput_bps

    comp = StatisticalAnalyzer.compare_conditions(results)
    assert comp.movement_time_reduction_pct > 30.0
    assert comp.throughput_gain_pct > 50.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
