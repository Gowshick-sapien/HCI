"""
Tri-Modal Weighted Confidence Fusion Subsystem.
Fuses heterogeneous confidence scores from Gaze, Head Pose, and Gesture modalities
under simplex weight constraints (sum w_i = 1.0, w_i >= 0).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple, Union
import numpy as np

from src.fusion.simplex_projection import SimplexProjectionEngine


@dataclass(frozen=True)
class FusedConfidenceMetrics:
    """Computed multimodal confidence aggregation metrics."""
    fused_confidence: float
    projected_weights: Tuple[float, float, float]
    fused_variance: float
    is_confident: bool
    dominant_modality: str


class ConfidenceFusionEngine:
    """
    Tri-modal confidence fusion coordinator.
    Evaluates Gaze, Head Pose, and Hand Gesture confidence streams.
    """

    MODALITY_NAMES = ["GAZE", "HEAD", "GESTURE"]

    def __init__(
        self,
        default_weights: Optional[Sequence[float]] = None,
        confidence_threshold: float = 0.65
    ) -> None:
        self.confidence_threshold = float(confidence_threshold)
        if default_weights is not None:
            self._default_weights = SimplexProjectionEngine.project_simplex_1d(default_weights)
        else:
            self._default_weights = np.array([0.40, 0.20, 0.40], dtype=np.float64)

    def fuse(
        self,
        s_gaze: float,
        s_head: float,
        s_gesture: float,
        weights: Optional[Union[np.ndarray, Sequence[float]]] = None,
        variances: Optional[Tuple[float, float, float]] = None
    ) -> FusedConfidenceMetrics:
        """
        Computes weighted fused confidence metric S_fused = w^T s.

        Args:
            s_gaze: Gaze confidence score in [0.0, 1.0].
            s_head: Head pose confidence score in [0.0, 1.0].
            s_gesture: Gesture classification confidence score in [0.0, 1.0].
            weights: Optional (3,) weight vector. If None, uses default weights.
            variances: Optional (3,) individual modality variances (sigma^2_gaze, sigma^2_head, sigma^2_gesture).

        Returns:
            FusedConfidenceMetrics instance.
        """
        # Clamp input scores to [0.0, 1.0]
        c_g = float(np.clip(s_gaze, 0.0, 1.0))
        c_h = float(np.clip(s_head, 0.0, 1.0))
        c_m = float(np.clip(s_gesture, 0.0, 1.0))
        scores = np.array([c_g, c_h, c_m], dtype=np.float64)

        # Enforce simplex projection on weights
        raw_w = weights if weights is not None else self._default_weights
        proj_w = SimplexProjectionEngine.project_simplex_1d(raw_w)

        # Weighted dot product
        s_fused = float(np.clip(np.dot(proj_w, scores), 0.0, 1.0))

        # Variance estimation
        if variances is not None:
            vars_arr = np.array(variances, dtype=np.float64)
            var_fused = float(np.sum((proj_w ** 2) * vars_arr))
        else:
            var_fused = 0.04

        # Determine dominant contributor
        weighted_contribs = proj_w * scores
        dom_idx = int(np.argmax(weighted_contribs))
        dom_modality = self.MODALITY_NAMES[dom_idx] if s_fused > 0.0 else "NONE"

        is_conf = s_fused >= self.confidence_threshold

        return FusedConfidenceMetrics(
            fused_confidence=s_fused,
            projected_weights=(float(proj_w[0]), float(proj_w[1]), float(proj_w[2])),
            fused_variance=var_fused,
            is_confident=is_conf,
            dominant_modality=dom_modality
        )


__all__ = ["ConfidenceFusionEngine", "FusedConfidenceMetrics"]
