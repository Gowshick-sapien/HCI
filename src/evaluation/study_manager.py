"""
Evaluation Subsystem: Latin Square Experimental Study Manager.
Coordinates counterbalanced 4x4 Williams Latin Square condition sequences,
target presentation geometries, and ISO 9241-9 trial metrics logging.
"""

from __future__ import annotations

import enum
import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


class ExperimentalCondition(str, enum.Enum):
    """Four experimental conditions evaluated in the user study."""
    C1_STATIC_BASELINE = "C1_STATIC_BASELINE"
    C2_HEURISTIC_RULES = "C2_HEURISTIC_RULES"
    C3_MICRO_SGD_ONLY = "C3_MICRO_SGD_ONLY"
    C4_FULL_ADAPTIVE = "C4_FULL_ADAPTIVE"


@dataclass(frozen=True)
class TrialTarget:
    """Target configuration for ISO 9241-9 pointing and selection trials."""
    target_id: int
    center_x: float
    center_y: float
    width: float
    height: float
    distance: float
    index_of_difficulty: float  # ID = log2(D/W + 1)


@dataclass
class TrialResult:
    """Data record captured for an individual pointing/selection trial."""
    participant_id: str
    condition: ExperimentalCondition
    block_index: int
    trial_index: int
    target_id: int
    index_of_difficulty: float
    movement_time_ms: float
    is_successful: bool
    error_count: int
    overshoot_count: int
    mean_gaze_confidence: float
    mean_head_confidence: float
    mean_hand_confidence: float
    effective_throughput: float  # TP = ID / (MT / 1000)
    timestamp: float = field(default_factory=time.time)


class StudyManager:
    """
    Manages counterbalanced Latin Square user studies across participants.
    Uses an orthogonal 4x4 Williams Latin Square matrix to eliminate first-order carryover effects.
    """

    # Orthogonal 4x4 Williams Latin Square condition matrix
    LATIN_SQUARE_MATRIX = [
        [ExperimentalCondition.C1_STATIC_BASELINE, ExperimentalCondition.C2_HEURISTIC_RULES,
         ExperimentalCondition.C4_FULL_ADAPTIVE, ExperimentalCondition.C3_MICRO_SGD_ONLY],
        [ExperimentalCondition.C2_HEURISTIC_RULES, ExperimentalCondition.C3_MICRO_SGD_ONLY,
         ExperimentalCondition.C1_STATIC_BASELINE, ExperimentalCondition.C4_FULL_ADAPTIVE],
        [ExperimentalCondition.C3_MICRO_SGD_ONLY, ExperimentalCondition.C4_FULL_ADAPTIVE,
         ExperimentalCondition.C2_HEURISTIC_RULES, ExperimentalCondition.C1_STATIC_BASELINE],
        [ExperimentalCondition.C4_FULL_ADAPTIVE, ExperimentalCondition.C1_STATIC_BASELINE,
         ExperimentalCondition.C3_MICRO_SGD_ONLY, ExperimentalCondition.C2_HEURISTIC_RULES],
    ]

    def __init__(
        self,
        trials_per_block: int = 16,
        screen_width: int = 1920,
        screen_height: int = 1080
    ) -> None:
        self.trials_per_block = max(4, int(trials_per_block))
        self.screen_width = int(screen_width)
        self.screen_height = int(screen_height)

        # Active session state
        self._current_participant: Optional[str] = None
        self._participant_index: int = 0
        self._condition_order: List[ExperimentalCondition] = []
        self._current_condition_idx: int = 0
        self._current_trial_idx: int = 0
        self._trial_start_time: float = 0.0
        self._session_results: List[TrialResult] = []

    def get_condition_sequence(self, participant_id: str) -> List[ExperimentalCondition]:
        """
        Returns the counterbalanced condition sequence for a given participant ID.
        Extracts participant number (e.g. 'P01' -> 0, 'P02' -> 1) modulo 4.
        """
        digits = "".join(ch for ch in participant_id if ch.isdigit())
        p_num = int(digits) - 1 if digits else 0
        row_idx = p_num % len(self.LATIN_SQUARE_MATRIX)
        return list(self.LATIN_SQUARE_MATRIX[row_idx])

    def start_session(self, participant_id: str) -> None:
        """Initializes a new participant study session."""
        self._current_participant = participant_id
        self._condition_order = self.get_condition_sequence(participant_id)
        self._current_condition_idx = 0
        self._current_trial_idx = 0
        self._session_results.clear()

    @property
    def current_condition(self) -> Optional[ExperimentalCondition]:
        """Returns the active experimental condition."""
        if not self._condition_order or self._current_condition_idx >= len(self._condition_order):
            return None
        return self._condition_order[self._current_condition_idx]

    @property
    def is_session_complete(self) -> bool:
        """Returns True if all 4 condition blocks have been completed."""
        return self._current_condition_idx >= len(self._condition_order)

    def generate_target(self, trial_index: int) -> TrialTarget:
        """
        Generates an ISO 9241-9 circular arrangement target coordinate.
        """
        center_x = self.screen_width / 2.0
        center_y = self.screen_height / 2.0
        radius = min(self.screen_width, self.screen_height) * 0.35
        target_size = 64.0  # 64px diameter

        num_targets = self.trials_per_block
        angle_rad = (2.0 * math.pi * trial_index) / num_targets

        tx = center_x + radius * math.cos(angle_rad)
        ty = center_y + radius * math.sin(angle_rad)

        distance = 2.0 * radius  # Opposite diameter crossing
        id_fitts = math.log2((distance / target_size) + 1.0)

        return TrialTarget(
            target_id=trial_index,
            center_x=tx,
            center_y=ty,
            width=target_size,
            height=target_size,
            distance=distance,
            index_of_difficulty=id_fitts
        )

    def record_trial(
        self,
        target: TrialTarget,
        movement_time_ms: float,
        is_successful: bool,
        error_count: int = 0,
        overshoot_count: int = 0,
        gaze_conf: float = 0.85,
        head_conf: float = 0.90,
        hand_conf: float = 0.88
    ) -> TrialResult:
        """
        Logs an individual trial result and advances the trial/block pointer.
        """
        if self._current_participant is None or self.current_condition is None:
            raise RuntimeError("Cannot record trial without active participant session.")

        mt_sec = max(0.001, movement_time_ms / 1000.0)
        throughput = target.index_of_difficulty / mt_sec if is_successful else 0.0

        result = TrialResult(
            participant_id=self._current_participant,
            condition=self.current_condition,
            block_index=self._current_condition_idx,
            trial_index=self._current_trial_idx,
            target_id=target.target_id,
            index_of_difficulty=target.index_of_difficulty,
            movement_time_ms=movement_time_ms,
            is_successful=is_successful,
            error_count=error_count,
            overshoot_count=overshoot_count,
            mean_gaze_confidence=gaze_conf,
            mean_head_confidence=head_conf,
            mean_hand_confidence=hand_conf,
            effective_throughput=throughput
        )

        self._session_results.append(result)
        self._current_trial_idx += 1

        # Advance to next condition block if trial block completed
        if self._current_trial_idx >= self.trials_per_block:
            self._current_trial_idx = 0
            self._current_condition_idx += 1

        return result

    def get_results(self) -> List[TrialResult]:
        """Returns all trial results captured in the active session."""
        return list(self._session_results)


__all__ = ["ExperimentalCondition", "TrialTarget", "TrialResult", "StudyManager"]
