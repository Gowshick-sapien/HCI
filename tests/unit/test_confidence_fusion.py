"""
Unit tests for Tri-Modal Weighted Confidence Fusion Engine.
"""

import numpy as np
import pytest

from src.fusion.confidence_fusion import ConfidenceFusionEngine


def test_confidence_fusion_weighted_average():
    fusion_engine = ConfidenceFusionEngine(default_weights=[0.5, 0.2, 0.3], confidence_threshold=0.60)

    # Test balanced confident inputs
    metrics = fusion_engine.fuse(s_gaze=0.80, s_head=0.90, s_gesture=0.70)
    # Expected: 0.5*0.8 + 0.2*0.9 + 0.3*0.7 = 0.40 + 0.18 + 0.21 = 0.79
    assert metrics.fused_confidence == pytest.approx(0.79, abs=1e-3)
    assert metrics.is_confident is True
    assert metrics.dominant_modality == "GAZE"


def test_confidence_fusion_suppression_when_blinking():
    fusion_engine = ConfidenceFusionEngine(default_weights=[0.4, 0.2, 0.4], confidence_threshold=0.65)

    # During eye blink: s_gaze = 0.0
    metrics = fusion_engine.fuse(s_gaze=0.0, s_head=0.80, s_gesture=0.70)
    # Expected: 0.4*0.0 + 0.2*0.8 + 0.4*0.7 = 0.16 + 0.28 = 0.44 (< 0.65 threshold)
    assert metrics.fused_confidence == pytest.approx(0.44, abs=1e-3)
    assert metrics.is_confident is False
