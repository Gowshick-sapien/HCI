"""
Stage 3A Multimodal Command Composer.
Binds Layer 1 spatial targets (WHERE: gaze_anchor) with Layer 1B intent semantics (WHAT: gesture_token)
into an immutable ComposedCommand contract.
Enforces the Gaze-Gesture Binding Invariant to eliminate Midas Touch misactivations.
"""

from __future__ import annotations

from typing import Optional, Tuple, Union
import numpy as np

from src.fusion.confidence_fusion import ConfidenceFusionEngine
from src.gesture.gesture_vocabulary import GestureVocabulary
from src.storage.schemas import (
    ActionType,
    ComposedCommand,
    GestureClassification,
    GestureToken,
    PerceptionFrame,
    ProfileSnapshot,
)


class CommandComposer:
    """
    Stage 3A Command Composition Engine.
    Fuses spatial perception with discrete gesture intent.
    """

    def __init__(
        self,
        vocabulary: Optional[GestureVocabulary] = None,
        confidence_fusion_engine: Optional[ConfidenceFusionEngine] = None,
    ) -> None:
        self.vocabulary = vocabulary or GestureVocabulary()
        self.fusion_engine = confidence_fusion_engine or ConfidenceFusionEngine()
        self._command_sequence: int = 0

    def compose(
        self,
        perception: PerceptionFrame,
        gesture: GestureClassification,
        profile: Optional[ProfileSnapshot] = None
    ) -> ComposedCommand:
        """
        Composes an immutable ComposedCommand from perception and gesture tokens.

        Args:
            perception: Layer 1 PerceptionFrame containing gaze and spatial anchor state.
            gesture: Arbitrated Layer 1B GestureClassification.
            profile: Optional user ProfileSnapshot.

        Returns:
            ComposedCommand instance.
        """
        self._command_sequence += 1
        cmd_id = f"cmd_{self._command_sequence:08d}"
        t_now = perception.timestamp_ms

        # Check for NONE token first
        if gesture.gesture_token == GestureToken.NONE:
            return ComposedCommand(
                action_id=cmd_id,
                action_type=ActionType.NO_ACTION,
                gaze_anchor=None,
                gesture_token=GestureToken.NONE,
                c_target=0.0,
                c_gesture=0.0,
                composed_score=0.0,
                requires_gaze_target=False,
                timestamp_ms=t_now
            )

        token_def = self.vocabulary.get_definition(gesture.gesture_token)
        requires_gaze = token_def.requires_gaze_target
        mapped_action = token_def.mapped_action

        # 1. Resolve modality weights from profile
        weights = None
        if profile and profile.modality_weights is not None:
            if isinstance(profile.modality_weights, dict):
                action_name = mapped_action.value if mapped_action else "PRIMARY_CLICK"
                weights = profile.modality_weights.get(action_name, [0.4, 0.2, 0.4])
            elif isinstance(profile.modality_weights, (list, tuple)):
                weights = profile.modality_weights

        # 2. Evaluate Multi-Source Confidence Fusion
        fused_metrics = self.fusion_engine.fuse(
            s_gaze=perception.gaze_confidence,
            s_head=perception.head_confidence,
            s_gesture=gesture.c_gesture,
            weights=weights
        )

        c_target = perception.gaze_confidence if perception.gaze_anchor is not None else 0.0
        c_gesture = gesture.c_gesture
        composed_score = fused_metrics.fused_confidence

        # 3. Binding Logic & Invariant Enforcement
        if token_def.is_rest_state:
            # REST state (FIST) -> zero action
            return ComposedCommand(
                action_id=cmd_id,
                action_type=ActionType.NO_ACTION,
                gaze_anchor=None,
                gesture_token=gesture.gesture_token,
                c_target=0.0,
                c_gesture=c_gesture,
                composed_score=0.0,
                requires_gaze_target=False,
                timestamp_ms=t_now
            )

        if requires_gaze:
            # Spatial Gesture (e.g. PINCH_INDEX, PINCH_MIDDLE, PINCH_HOLD)
            # Invariant INV-D3.1: Spatial clicks MUST be bound to a locked gaze anchor
            if perception.gaze_anchor is not None:
                action_type = mapped_action
                anchor = perception.gaze_anchor
            else:
                # Unanchored spatial gesture -> suppress execution to prevent accidental clicks
                action_type = ActionType.NO_ACTION
                anchor = None
        else:
            # Global Non-Spatial Gesture (e.g. OPEN_PALM, THUMBS_UP, SWIPE_LEFT)
            action_type = mapped_action
            anchor = None

        return ComposedCommand(
            action_id=cmd_id,
            action_type=action_type,
            gaze_anchor=anchor,
            gesture_token=gesture.gesture_token,
            c_target=c_target,
            c_gesture=c_gesture,
            composed_score=composed_score,
            requires_gaze_target=requires_gaze,
            timestamp_ms=t_now
        )


__all__ = ["CommandComposer"]
