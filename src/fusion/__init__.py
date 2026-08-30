"""
Layer 3 & Stage 3A Multimodal Fusion and Command Composition Subsystem.
Provides exact box-constrained simplex projection, tri-modal confidence fusion,
and Gaze-Gesture spatial-intent command composition.
"""

from src.fusion.simplex_projection import SimplexProjectionEngine
from src.fusion.confidence_fusion import (
    ConfidenceFusionEngine,
    FusedConfidenceMetrics,
)
from src.fusion.command_composer import CommandComposer

__all__ = [
    "SimplexProjectionEngine",
    "ConfidenceFusionEngine",
    "FusedConfidenceMetrics",
    "CommandComposer",
]
