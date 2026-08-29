"""
Unit tests for Gaze Dwell Tracker and Fixation Analysis.
"""

import pytest
from src.perception.gaze_dwell_tracker import GazeDwellTracker


def test_gaze_dwell_accumulation_and_anchor():
    """Invariant INV-D1.4: gaze_anchor only declared when dwell >= tau_dwell."""
    tracker = GazeDwellTracker(fixation_radius_px=85.0, default_tau_dwell_ms=120.0)
    
    # 1. First fixation frame at t=0
    m1 = tracker.update((500.0, 500.0), timestamp_ms=0.0)
    assert m1.gaze_dwell_ms == 0.0
    assert m1.gaze_anchor is None
    assert m1.is_fixating is True

    # 2. Fixation held at t=40ms (< 120ms threshold)
    m2 = tracker.update((505.0, 495.0), timestamp_ms=40.0)
    assert m2.gaze_dwell_ms == 40.0
    assert m2.gaze_anchor is None

    # 3. Fixation held at t=80ms (< 120ms threshold)
    m3 = tracker.update((502.0, 498.0), timestamp_ms=80.0)
    assert m3.gaze_dwell_ms == 80.0
    assert m3.gaze_anchor is None

    # 4. Fixation crosses 120ms threshold at t=130ms
    m4 = tracker.update((500.0, 500.0), timestamp_ms=130.0)
    assert m4.gaze_dwell_ms == 130.0
    assert m4.gaze_anchor is not None
    assert abs(m4.gaze_anchor[0] - 500.0) < 10.0
    assert abs(m4.gaze_anchor[1] - 500.0) < 10.0
    assert m4.gaze_stability >= 0.80


def test_gaze_dwell_saccade_reset():
    """Verifies that moving gaze outside fixation radius resets dwell accumulator."""
    tracker = GazeDwellTracker(fixation_radius_px=85.0, default_tau_dwell_ms=120.0)
    
    # Fixate at (500, 500) across consecutive frames
    tracker.update((500.0, 500.0), timestamp_ms=0.0)
    tracker.update((500.0, 500.0), timestamp_ms=50.0)
    tracker.update((500.0, 500.0), timestamp_ms=100.0)
    m = tracker.update((500.0, 500.0), timestamp_ms=150.0)
    assert m.gaze_anchor is not None

    # Saccade to (900, 900) (> 1.4 * 85px away) for 2 consecutive frames
    tracker.update((900.0, 900.0), timestamp_ms=180.0)
    m_saccade = tracker.update((900.0, 900.0), timestamp_ms=210.0)
    assert m_saccade.gaze_dwell_ms == 0.0
    assert m_saccade.gaze_anchor is None
    assert m_saccade.is_fixating is False
