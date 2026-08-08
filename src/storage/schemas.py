"""
Core Data Schemas and Immutable Contracts.
Defines strongly-typed dataclasses and enums for all 6 layers of the closed-loop architecture.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import json
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


class ActionTier(str, Enum):
    """Execution safety tiers for multimodal desktop actions."""
    TIER_1_IMMEDIATE = "TIER_1_IMMEDIATE"
    TIER_2_SAFETY_GATED = "TIER_2_SAFETY_GATED"


class ActionType(str, Enum):
    """Taxonomy of supported desktop interaction commands."""
    SCROLL_UP = "SCROLL_UP"
    SCROLL_DOWN = "SCROLL_DOWN"
    NAVIGATE_PREVIOUS = "NAVIGATE_PREVIOUS"
    NAVIGATE_NEXT = "NAVIGATE_NEXT"
    ZOOM_IN = "ZOOM_IN"
    ZOOM_OUT = "ZOOM_OUT"
    PRIMARY_CLICK = "PRIMARY_CLICK"
    CLOSE_ACTIVE_WINDOW = "CLOSE_ACTIVE_WINDOW"
    CONFIRM_SUBMIT = "CONFIRM_SUBMIT"
    NO_ACTION = "NO_ACTION"


class FeedbackWindow(str, Enum):
    """Temporal observation window stages for implicit feedback."""
    REFRACTORY = "REFRACTORY"
    CORRECTION = "CORRECTION"
    STABILITY_EXPIRATION = "STABILITY_EXPIRATION"
    RESOLVED = "RESOLVED"


class FeedbackType(str, Enum):
    """Supervisory feedback polarity."""
    IMPLICIT_POS = "IMPLICIT_POS"
    IMPLICIT_NEG = "IMPLICIT_NEG"


class FailureMode(str, Enum):
    """7-mode failure taxonomy for diagnostic governance."""
    NONE = "NONE"
    FALSE_ACTIVATION = "FALSE_ACTIVATION"
    FALSE_REJECTION = "FALSE_REJECTION"
    WRONG_TARGET = "WRONG_TARGET"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    DELAYED_RESPONSE = "DELAYED_RESPONSE"
    USER_OVERRIDE = "USER_OVERRIDE"
    ENVIRONMENTAL_DRIFT = "ENVIRONMENTAL_DRIFT"


class FailureSeverity(int, Enum):
    """Severity grading for interaction failures (Level 1 to Level 5)."""
    SEV_1_BENIGN = 1
    SEV_2_MINOR = 2
    SEV_3_MODERATE = 3
    SEV_4_SIGNIFICANT = 4
    SEV_5_CRITICAL = 5


class GatekeeperVerdict(str, Enum):
    """Layer 5 validation decisions for online parameter updates."""
    APPROVE = "APPROVE"
    REJECT = "REJECT"


class MacroPolicy(str, Enum):
    """Macro-adaptation state machine transition policies."""
    MERGE = "MERGE"
    FREEZE = "FREEZE"
    DISCARD = "DISCARD"
    RECALIBRATE = "RECALIBRATE"


class SystemHealthState(str, Enum):
    """Runtime system state badge for explainability HUD and telemetry."""
    BOOTSTRAPPING = "BOOTSTRAPPING"
    LEARNING = "LEARNING"
    IMPROVING = "IMPROVING"
    STABLE = "STABLE"
    DRIFTING = "DRIFTING"
    RECOVERING = "RECOVERING"


@dataclass(frozen=True)
class RawFrame:
    """Captured video frame metadata and image container."""
    frame_id: int
    timestamp: float
    width: int = 1280
    height: int = 720
    ambient_lux: float = 50.0
    capture_latency_ms: float = 0.0
    image: Optional[np.ndarray] = field(default=None, repr=False)


@dataclass(frozen=True)
class EyeLandmarks:
    """Ocular gaze and iris tracking features."""
    left_iris_center: Tuple[float, float]
    right_iris_center: Tuple[float, float]
    left_ear: float
    right_ear: float
    iris_ratio_x: float
    iris_ratio_y: float
    confidence: float
    variance: float = 0.05


@dataclass(frozen=True)
class HeadPoseLandmarks:
    """3D head pose orientation and rotation features."""
    yaw: float
    pitch: float
    roll: float
    translation_vector: Tuple[float, float, float]
    mahalanobis_distance: float
    confidence: float
    variance: float = 0.05


@dataclass(frozen=True)
class HandLandmarks:
    """21-point 3D hand tracking kinematics and gesture features."""
    is_detected: bool
    pinch_distance: float
    palm_normal: Tuple[float, float, float]
    wrist_position: Tuple[float, float, float]
    wrist_velocity: float
    gesture_class: str
    confidence: float
    variance: float = 0.05


@dataclass(frozen=True)
class FeatureVector:
    """Unified multimodal feature vector x passed across the closed loop."""
    timestamp: float
    frame_id: int
    eye: EyeLandmarks
    head: HeadPoseLandmarks
    hand: HandLandmarks
    scores_array: Tuple[float, float, float] # (s_gaze, s_head, s_hand)
    variance_array: Tuple[float, float, float] # (var_gaze, var_head, var_hand)
    ambient_lux: float = 50.0
    user_distance_mm: float = 600.0

    def to_numpy_scores(self) -> np.ndarray:
        return np.array(self.scores_array, dtype=np.float64)

    def to_numpy_variances(self) -> np.ndarray:
        return np.array(self.variance_array, dtype=np.float64)


@dataclass(frozen=True)
class ActionCandidate:
    """Intent candidate evaluated during late fusion."""
    action_name: str
    tier: ActionTier
    fused_score: float
    activation_threshold: float
    score_margin: float
    is_activated: bool
    dwell_required_ms: float
    timestamp: float


@dataclass(frozen=True)
class ActionContext:
    """Immutable context record dispatched upon action execution."""
    action_id: str
    action_name: str
    tier: ActionTier
    timestamp_t0: float
    target_pid: int
    target_window_title: str
    feature_snapshot: FeatureVector
    weights_snapshot: Dict[str, float]
    fused_score: float
    threshold: float
    is_executed: bool = False
    execution_latency_ms: float = 0.0


@dataclass(frozen=True)
class FeedbackEvent:
    """Supervisory feedback event inferred by Layer 4 implicit observation."""
    feedback_id: str
    action_id: str
    timestamp: float
    latency_delta_t: float
    feedback_type: FeedbackType
    confidence_cfb: float
    failure_mode: FailureMode
    severity: FailureSeverity
    detector_source: str
    raw_event_payload: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GatekeeperDecision:
    """Layer 5 gatekeeper validation verdict for online micro-SGD updates."""
    verdict: GatekeeperVerdict
    rejection_reason: Optional[str]
    sample_count: int
    confidence_cfb: float
    sprt_score: float
    effective_learning_rate_scale: float


@dataclass(frozen=True)
class AssessmentMetrics:
    """Runtime assessment health metrics computed by Engine 5A."""
    timestamp: float
    interactions_count: int
    adaptation_gain_ewma: float
    learning_velocity: float
    weight_stability_index: float
    adaptation_confidence_index: float
    expected_calibration_error: float
    recovery_rate: float
    drift_recovery_time: float
    health_state: SystemHealthState


@dataclass
class ProfileSnapshot:
    """Master persistent user profile state snapshot."""
    user_id: str
    version_id: int
    timestamp_epoch: float
    session_id: str
    is_session_boundary: bool
    modality_weights: Dict[str, List[float]]
    action_thresholds: Dict[str, float]
    gaze_calibration_matrix: List[List[float]]
    neutral_pose_mean: List[float]
    neutral_pose_cov_inv: List[List[float]]
    user_latency_tempo_tau: float
    running_score_stats: Dict[str, Dict[str, float]]
    adaptation_confidence_index: float
    weight_stability_index: float
    expected_calibration_error: float
    cumulative_adaptation_gain: float
    total_interactions_seen: int
    total_updates_approved: int
    total_updates_rejected: int
    failure_counts_by_taxonomy: Dict[str, int]
    wald_sprt_score: float
    last_recalibration_timestamp: float
    recalibration_count: int
    baseline_ambient_lux: float
    baseline_user_distance_mm: float

    def to_dict(self) -> Dict[str, Any]:
        """Serialize profile snapshot to a standard dictionary."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Serialize profile snapshot to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProfileSnapshot:
        """Instantiate profile snapshot from dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> ProfileSnapshot:
        """Instantiate profile snapshot from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def create_default(cls, user_id: str = "default_user", session_id: str = "session_0") -> ProfileSnapshot:
        """Generate default initial bootstrap profile."""
        default_actions = [
            "SCROLL_UP", "SCROLL_DOWN", "NAVIGATE_PREVIOUS", "NAVIGATE_NEXT",
            "ZOOM_IN", "ZOOM_OUT", "PRIMARY_CLICK", "CLOSE_ACTIVE_WINDOW", "CONFIRM_SUBMIT"
        ]
        return cls(
            user_id=user_id,
            version_id=1,
            timestamp_epoch=time.time(),
            session_id=session_id,
            is_session_boundary=True,
            modality_weights={
                "SCROLL_UP": [0.40, 0.40, 0.20],
                "SCROLL_DOWN": [0.40, 0.40, 0.20],
                "NAVIGATE_PREVIOUS": [0.30, 0.30, 0.40],
                "NAVIGATE_NEXT": [0.30, 0.30, 0.40],
                "ZOOM_IN": [0.20, 0.30, 0.50],
                "ZOOM_OUT": [0.20, 0.30, 0.50],
                "PRIMARY_CLICK": [0.35, 0.25, 0.40],
                "CLOSE_ACTIVE_WINDOW": [0.20, 0.30, 0.50],
                "CONFIRM_SUBMIT": [0.30, 0.30, 0.40]
            },
            action_thresholds={
                "SCROLL_UP": 0.55,
                "SCROLL_DOWN": 0.55,
                "NAVIGATE_PREVIOUS": 0.60,
                "NAVIGATE_NEXT": 0.60,
                "ZOOM_IN": 0.65,
                "ZOOM_OUT": 0.65,
                "PRIMARY_CLICK": 0.70,
                "CLOSE_ACTIVE_WINDOW": 0.80,
                "CONFIRM_SUBMIT": 0.75
            },
            gaze_calibration_matrix=[
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0]
            ],
            neutral_pose_mean=[0.0, 0.0, 0.0],
            neutral_pose_cov_inv=[
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0]
            ],
            user_latency_tempo_tau=0.60,
            running_score_stats={
                a: {"mean": 0.50, "std": 0.15, "count": 0} for a in default_actions
            },
            adaptation_confidence_index=0.0,
            weight_stability_index=0.0,
            expected_calibration_error=0.0,
            cumulative_adaptation_gain=0.0,
            total_interactions_seen=0,
            total_updates_approved=0,
            total_updates_rejected=0,
            failure_counts_by_taxonomy={
                mode.value: 0 for mode in FailureMode if mode != FailureMode.NONE
            },
            wald_sprt_score=0.0,
            last_recalibration_timestamp=0.0,
            recalibration_count=0,
            baseline_ambient_lux=50.0,
            baseline_user_distance_mm=600.0
        )
