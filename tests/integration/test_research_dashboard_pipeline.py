"""
Integration test for Research Dashboard Pipeline (Deliverable E3).
Verifies Invariant INV-E3.7: End-to-end telemetry ingestion, study session execution, and automated report synthesis.
"""

import os
import sys
import tempfile
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
from PySide6.QtWidgets import QApplication

from src.assessment.session_report_generator import SessionReportGenerator
from src.evaluation.study_manager import ExperimentalCondition, StudyManager
from src.storage.schemas import (
    ActionContext,
    ActionTier,
    AssessmentMetrics,
    FailureMode,
    FailureSeverity,
    FeedbackEvent,
    FeedbackType,
    GatekeeperDecision,
    GatekeeperVerdict,
    SystemHealthState,
)
from src.ui.research_dashboard import ResearchDashboardWindow


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_research_dashboard_pipeline_integration(qapp):
    """Invariant INV-E3.7: Ingests events, simulates Latin Square study, and generates report."""
    window = ResearchDashboardWindow()
    window.show()

    # 1. Ingest action & feedback events into dashboard
    action = ActionContext(
        action_id="cmd_int_01",
        action_name="PRIMARY_CLICK",
        tier=ActionTier.TIER_1_IMMEDIATE,
        timestamp_t0=time.time(),
        target_pid=1001,
        target_window_title="Research App",
        feature_snapshot=None,
        weights_snapshot={"EYE": 0.42, "HEAD": 0.28, "HAND": 0.30},
        fused_score=0.86,
        threshold=0.70,
        is_executed=True
    )
    window.push_action_event(action)

    fb = FeedbackEvent(
        feedback_id="fb_int_01",
        action_id="cmd_int_01",
        timestamp=time.time(),
        latency_delta_t=0.42,
        feedback_type=FeedbackType.IMPLICIT_NEG,
        confidence_cfb=0.80,
        failure_mode=FailureMode.USER_OVERRIDE,
        severity=FailureSeverity.SEV_2_MINOR,
        detector_source="IMPLICIT_MOUSE_TAKEOVER"
    )
    decision = GatekeeperDecision(
        verdict=GatekeeperVerdict.APPROVE,
        rejection_reason=None,
        sample_count=4,
        confidence_cfb=0.80,
        sprt_score=2.95,
        effective_learning_rate_scale=1.0
    )
    window.push_feedback_event(fb, decision, sprt_score=2.95)

    metrics = AssessmentMetrics(
        timestamp=time.time(),
        interactions_count=20,
        adaptation_gain_ewma=0.05,
        learning_velocity=0.02,
        weight_stability_index=0.88,
        adaptation_confidence_index=0.84,
        expected_calibration_error=0.05,
        recovery_rate=1.0,
        drift_recovery_time=0.0,
        health_state=SystemHealthState.STABLE
    )
    window.push_metrics_update(metrics, weights={"EYE": 0.40, "HEAD": 0.30, "HAND": 0.30})
    window._drain_event_queues()

    # Verify table has 2 records
    assert window.tab_telemetry.model.rowCount() == 2

    # 2. Simulate study execution and report generation in temp directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        report_gen = SessionReportGenerator(output_dir=tmp_dir)
        study_mgr = StudyManager(trials_per_block=4)
        study_mgr.start_session("P01")

        while not study_mgr.is_session_complete:
            trial_idx = study_mgr._current_trial_idx
            target = study_mgr.generate_target(trial_idx)
            study_mgr.record_trial(
                target=target,
                movement_time_ms=500.0,
                is_successful=True,
                gaze_conf=0.90,
                head_conf=0.92,
                hand_conf=0.88
            )

        results = study_mgr.get_results()
        assert len(results) == 16  # 4 blocks * 4 trials

        rep_file = report_gen.generate_markdown_report("P01", results, metrics=metrics)
        assert os.path.exists(rep_file)
        with open(rep_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert "# Empirical User Study Session Report" in content
        assert "Wilcoxon Signed-Rank Test" in content

    window.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
