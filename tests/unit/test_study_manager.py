"""
Unit tests for Latin Square StudyManager (Deliverable E3).
Verifies Invariant INV-E3.5: Counterbalanced condition sequence generation and orthogonal matrix assignment.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
from src.evaluation.study_manager import ExperimentalCondition, StudyManager, TrialTarget


def test_latin_square_counterbalancing_orthogonality():
    """Invariant INV-E3.5: All 4 conditions appear exactly once per participant row in Latin Square ordering."""
    manager = StudyManager(trials_per_block=8)

    participants = ["P01", "P02", "P03", "P04"]
    all_conditions = set(ExperimentalCondition)

    seen_orders = []
    for pid in participants:
        seq = manager.get_condition_sequence(pid)
        assert len(seq) == 4
        assert set(seq) == all_conditions, f"Participant {pid} missing conditions: {seq}"
        seen_orders.append(tuple(seq))

    # All 4 participants should have distinct counterbalanced orders
    assert len(set(seen_orders)) == 4


def test_study_manager_trial_progression():
    """Verifies that trial generation, recording, and block advancement work properly."""
    manager = StudyManager(trials_per_block=4)
    manager.start_session("P01")

    assert manager.current_condition == ExperimentalCondition.C1_STATIC_BASELINE
    assert not manager.is_session_complete

    # Record 4 trials for block 0 (Condition 1)
    for i in range(4):
        target = manager.generate_target(i)
        assert target.index_of_difficulty > 0.0
        res = manager.record_trial(target=target, movement_time_ms=500.0, is_successful=True)
        assert res.effective_throughput > 0.0

    # Advance to block 1 (Condition 2)
    assert manager.current_condition == ExperimentalCondition.C2_HEURISTIC_RULES
    assert len(manager.get_results()) == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
