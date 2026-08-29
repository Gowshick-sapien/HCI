"""
Pytest Test Fixtures and Synthetic Generators.
Provides deterministic mock video frames, feature vectors, action contexts, perception frames, and profile snapshots.
"""

import time
from typing import Dict, List, Tuple
import numpy as np
import pytest

from src.storage.schemas import (
    ActionCandidate,
    ActionContext,
    ActionTier,
    ActionType,
    AssessmentMetrics,
    EyeLandmarks,
    FailureMode,
    FailureSeverity,
    FeatureVector,
    FeedbackEvent,
    FeedbackType,
    GestureClassification,
    GestureToken,
    HandLandmarks,
    HeadPoseLandmarks,
    PerceptionFrame,
    ProfileSnapshot,
    RawFrame,
    SystemHealthState,
)


@pytest.fixture
def mock_raw_frame() -> RawFrame:
    """Returns a synthetic 720p RawFrame instance."""
    dummy_img = np.zeros((720, 1280, 3), dtype=np.uint8)
    return RawFrame(
        frame_id=101,
        timestamp=time.time(),
        width=1280,
        height=720,
        ambient_lux=45.0,
        capture_latency_ms=3.2,
        image=dummy_img
    )


@pytest.fixture
def mock_eye_landmarks() -> EyeLandmarks:
    """Returns a synthetic EyeLandmarks instance with neutral gaze coordinates."""
    return EyeLandmarks(
        left_iris_center=(0.52, 0.48),
        right_iris_center=(0.48, 0.48),
        left_ear=0.28,
        right_ear=0.28,
        iris_ratio_x=0.50,
        iris_ratio_y=0.50,
        confidence=0.92,
        variance=0.03
    )


@pytest.fixture
def mock_head_landmarks() -> HeadPoseLandmarks:
    """Returns a synthetic HeadPoseLandmarks instance with neutral orientation."""
    return HeadPoseLandmarks(
        yaw=1.5,
        pitch=-2.0,
        roll=0.5,
        translation_vector=(0.0, 0.0, 600.0),
        mahalanobis_distance=1.2,
        confidence=0.95,
        variance=0.02
    )


@pytest.fixture
def mock_hand_landmarks() -> HandLandmarks:
    """Returns a synthetic HandLandmarks instance with pinch gesture."""
    # 21 synthetic landmarks for pinch
    raw_lms = [(0.5, 0.5, 0.0)] * 21
    # Index tip and thumb tip close together
    raw_lms[4] = (0.50, 0.50, 0.0) # thumb tip
    raw_lms[8] = (0.51, 0.51, 0.0) # index tip
    
    return HandLandmarks(
        is_detected=True,
        pinch_distance=0.014,
        palm_normal=(0.0, 0.0, -1.0),
        wrist_position=(0.5, 0.7, 0.4),
        wrist_velocity=1.2,
        gesture_class="PINCH_INDEX",
        confidence=0.88,
        variance=0.04,
        raw_landmarks_21=raw_lms
    )


@pytest.fixture
def mock_perception_frame(
    mock_eye_landmarks: EyeLandmarks,
    mock_head_landmarks: HeadPoseLandmarks,
    mock_hand_landmarks: HandLandmarks
) -> PerceptionFrame:
    """Returns an immutable PerceptionFrame instance."""
    return PerceptionFrame(
        timestamp_ms=time.time() * 1000.0,
        frame_id=101,
        eye=mock_eye_landmarks,
        head=mock_head_landmarks,
        hand=mock_hand_landmarks,
        gaze_confidence=0.92,
        head_confidence=0.95,
        gaze_screen_xy=(960.0, 540.0),
        head_euler_angles=(1.5, -2.0, 0.5),
        gaze_dwell_ms=250.0,
        gaze_stability=0.94,
        gaze_anchor=(960.0, 540.0),
        sensor_covariance_matrix=np.diag([0.03, 0.02]),
        ambient_illuminance_lux=50.0,
        eye_aspect_ratio=0.28
    )


@pytest.fixture
def mock_feature_vector(
    mock_eye_landmarks: EyeLandmarks,
    mock_head_landmarks: HeadPoseLandmarks,
    mock_hand_landmarks: HandLandmarks
) -> FeatureVector:
    """Returns a unified FeatureVector instance."""
    return FeatureVector(
        timestamp=time.time(),
        frame_id=101,
        eye=mock_eye_landmarks,
        head=mock_head_landmarks,
        hand=mock_hand_landmarks,
        scores_array=(0.92, 0.95, 0.88),
        variance_array=(0.03, 0.02, 0.04),
        ambient_lux=45.0,
        user_distance_mm=600.0
    )


@pytest.fixture
def mock_action_context(mock_perception_frame: PerceptionFrame) -> ActionContext:
    """Returns an executed ActionContext instance."""
    return ActionContext(
        action_id="act_test_001",
        action_name="PRIMARY_CLICK",
        tier=ActionTier.TIER_1_IMMEDIATE,
        timestamp_t0=time.time() - 0.5,
        target_pid=1234,
        target_window_title="Browser Window",
        feature_snapshot=mock_perception_frame,
        weights_snapshot={"PRIMARY_CLICK": 0.60},
        fused_score=0.78,
        threshold=0.70,
        is_executed=True,
        execution_latency_ms=1.5
    )


@pytest.fixture
def mock_feedback_event() -> FeedbackEvent:
    """Returns an implicit negative feedback event."""
    return FeedbackEvent(
        feedback_id="fb_test_001",
        action_id="act_test_001",
        timestamp=time.time(),
        latency_delta_t=0.65,
        feedback_type=FeedbackType.IMPLICIT_NEG,
        confidence_cfb=0.82,
        failure_mode=FailureMode.FALSE_ACTIVATION,
        severity=FailureSeverity.SEV_2_MINOR,
        detector_source="GlobalUndoHookDetector",
        raw_event_payload={"hotkey": "Ctrl+Z"}
    )


@pytest.fixture
def mock_profile_snapshot() -> ProfileSnapshot:
    """Returns a default ProfileSnapshot instance."""
    return ProfileSnapshot.create_default(user_id="test_user", session_id="test_session")


@pytest.fixture
def mock_assessment_metrics() -> AssessmentMetrics:
    """Returns a baseline AssessmentMetrics instance."""
    return AssessmentMetrics(
        timestamp=time.time(),
        interactions_count=25,
        adaptation_gain_ewma=0.08,
        learning_velocity=0.02,
        weight_stability_index=0.015,
        adaptation_confidence_index=0.82,
        expected_calibration_error=0.04,
        recovery_rate=0.75,
        drift_recovery_time=0.0,
        health_state=SystemHealthState.STABLE
    )
