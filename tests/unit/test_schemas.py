"""
Unit Tests for Core Schemas and Invariants.
Verifies data immutability, type assertions, serialization, and default profile construction.
"""

from dataclasses import FrozenInstanceError
import json
import pytest

from src.storage.schemas import (
    ActionCandidate,
    ActionContext,
    ActionTier,
    ActionType,
    AssessmentMetrics,
    FailureMode,
    FeatureVector,
    FeedbackEvent,
    FeedbackType,
    ProfileSnapshot,
    RawFrame,
    SystemHealthState,
)


def test_raw_frame_immutability(mock_raw_frame: RawFrame):
    """RawFrame must be frozen to prevent in-place mutation across threads."""
    assert mock_raw_frame.frame_id == 101
    with pytest.raises(FrozenInstanceError):
        mock_raw_frame.frame_id = 999  # type: ignore


def test_feature_vector_numpy_conversion(mock_feature_vector: FeatureVector):
    """FeatureVector must correctly convert scores and variances to numpy arrays."""
    scores = mock_feature_vector.to_numpy_scores()
    variances = mock_feature_vector.to_numpy_variances()

    assert scores.shape == (3,)
    assert variances.shape == (3,)
    assert float(scores[0]) == pytest.approx(0.92)
    assert float(scores[1]) == pytest.approx(0.95)
    assert float(scores[2]) == pytest.approx(0.88)


def test_action_context_immutability(mock_action_context: ActionContext):
    """ActionContext must be frozen and hold valid execution properties."""
    assert mock_action_context.action_name in ["PRIMARY_CLICK", "SCROLL_DOWN"]
    assert mock_action_context.tier == ActionTier.TIER_1_IMMEDIATE
    assert mock_action_context.is_executed is True

    with pytest.raises(FrozenInstanceError):
        mock_action_context.fused_score = 1.0  # type: ignore


def test_feedback_event_properties(mock_feedback_event: FeedbackEvent):
    """FeedbackEvent must preserve detector source and confidence bounds."""
    assert mock_feedback_event.feedback_type == FeedbackType.IMPLICIT_NEG
    assert mock_feedback_event.failure_mode == FailureMode.FALSE_ACTIVATION
    assert 0.0 <= mock_feedback_event.confidence_cfb <= 1.0
    assert mock_feedback_event.detector_source == "GlobalUndoHookDetector"


def test_profile_snapshot_serialization(mock_profile_snapshot: ProfileSnapshot):
    """ProfileSnapshot must correctly round-trip through dictionary and JSON serialization."""
    json_str = mock_profile_snapshot.to_json()
    assert isinstance(json_str, str)

    restored = ProfileSnapshot.from_json(json_str)
    assert restored.user_id == mock_profile_snapshot.user_id
    assert restored.version_id == mock_profile_snapshot.version_id
    assert restored.modality_weights == mock_profile_snapshot.modality_weights
    assert restored.action_thresholds == mock_profile_snapshot.action_thresholds
    assert len(restored.gaze_calibration_matrix) == 2
    assert len(restored.neutral_pose_cov_inv) == 3


def test_profile_snapshot_weights_sum_to_one(mock_profile_snapshot: ProfileSnapshot):
    """All action modality weights in initial profile must sum to 1.0 within numerical tolerance."""
    for action_name, weights in mock_profile_snapshot.modality_weights.items():
        assert len(weights) == 3
        assert sum(weights) == pytest.approx(1.0, abs=1e-5), f"Weights for {action_name} do not sum to 1.0"
        for w in weights:
            assert 0.05 <= w <= 0.85, f"Weight {w} outside [0.05, 0.85] for {action_name}"


def test_assessment_metrics_invariants(mock_assessment_metrics: AssessmentMetrics):
    """AssessmentMetrics must accurately report valid health state and bounded metrics."""
    assert mock_assessment_metrics.health_state == SystemHealthState.STABLE
    assert 0.0 <= mock_assessment_metrics.adaptation_confidence_index <= 1.0
    assert mock_assessment_metrics.expected_calibration_error >= 0.0
