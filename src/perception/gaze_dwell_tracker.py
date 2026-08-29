"""
Gaze Dwell Tracker and Fixation Analysis Sub-Module.
Tracks temporal gaze dwell accumulation, spatial fixation stability,
and determines valid screen anchor targets to prevent reading gaze false activations.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Optional, Tuple
import numpy as np


@dataclass(frozen=True)
class GazeDwellMetrics:
    """Computed gaze fixation metrics for a single frame."""
    gaze_dwell_ms: float
    gaze_stability: float
    gaze_anchor: Optional[Tuple[float, float]]
    is_fixating: bool


class GazeDwellTracker:
    """
    Temporal gaze fixation and dwell accumulator.
    Maintains a sliding window of gaze points to evaluate stability and declare stable screen anchors.
    Accommodates normal foveal eye fixation span (~2 degrees / 85 px at 60cm distance).
    """

    def __init__(
        self,
        fixation_radius_px: float = 85.0,
        window_duration_ms: float = 150.0,
        default_tau_dwell_ms: float = 120.0
    ) -> None:
        self.fixation_radius_px = float(fixation_radius_px)
        self.window_duration_ms = float(window_duration_ms)
        self.default_tau_dwell_ms = float(default_tau_dwell_ms)

        # Sliding window buffer of (timestamp_ms, u, v)
        self._history: Deque[Tuple[float, float, float]] = deque()
        
        # Active fixation state
        self._fixation_center: Optional[Tuple[float, float]] = None
        self._fixation_start_ms: float = 0.0
        self._accumulated_dwell_ms: float = 0.0
        self._consecutive_outlier_count: int = 0
        self._last_timestamp_ms: Optional[float] = None

    def reset(self) -> None:
        """Resets tracker state and clears history."""
        self._history.clear()
        self._fixation_center = None
        self._fixation_start_ms = 0.0
        self._accumulated_dwell_ms = 0.0
        self._consecutive_outlier_count = 0
        self._last_timestamp_ms = None

    def update(
        self,
        gaze_xy: Optional[Tuple[float, float]],
        timestamp_ms: float,
        tau_dwell_ms: Optional[float] = None
    ) -> GazeDwellMetrics:
        """
        Updates the dwell tracker with new gaze coordinates.

        Args:
            gaze_xy: Screen coordinates (u, v) in pixels, or None if gaze is lost / blink.
            timestamp_ms: Current frame timestamp in milliseconds.
            tau_dwell_ms: User-calibrated minimum dwell threshold. If None, uses default.

        Returns:
            GazeDwellMetrics containing dwell duration, stability score, and optional declared anchor.
        """
        threshold = tau_dwell_ms if tau_dwell_ms is not None else self.default_tau_dwell_ms

        if gaze_xy is None:
            # Gaze lost (e.g. blink or tracking lost) -> decay dwell gracefully
            self._accumulated_dwell_ms = max(0.0, self._accumulated_dwell_ms - 40.0)
            self._last_timestamp_ms = timestamp_ms
            return GazeDwellMetrics(
                gaze_dwell_ms=self._accumulated_dwell_ms,
                gaze_stability=0.0,
                gaze_anchor=None,
                is_fixating=False
            )

        u, v = float(gaze_xy[0]), float(gaze_xy[1])
        delta_t = (timestamp_ms - self._last_timestamp_ms) if self._last_timestamp_ms is not None else 33.3
        delta_t = max(0.0, min(delta_t, 100.0))
        self._last_timestamp_ms = timestamp_ms

        # 1. Update temporal history window
        self._history.append((timestamp_ms, u, v))
        cutoff_ms = timestamp_ms - self.window_duration_ms
        while self._history and self._history[0][0] < cutoff_ms:
            self._history.popleft()

        # 2. Compute spatial stability over history window
        if len(self._history) >= 3:
            pts = np.array([(p[1], p[2]) for p in self._history], dtype=np.float64)
            center = np.mean(pts, axis=0)
            var_dist = float(np.mean(np.sum((pts - center) ** 2, axis=1)))
            r_sq = self.fixation_radius_px ** 2
            stability = float(np.exp(-var_dist / max(1.0, r_sq)))
        else:
            stability = 1.0

        # 3. Evaluate fixation center distance
        if self._fixation_center is None:
            self._fixation_center = (u, v)
            self._fixation_start_ms = timestamp_ms
            self._accumulated_dwell_ms = 0.0
            self._consecutive_outlier_count = 0
            is_fixating = True
        else:
            dist = float(np.sqrt((u - self._fixation_center[0]) ** 2 + (v - self._fixation_center[1]) ** 2))
            
            if dist <= self.fixation_radius_px:
                # Within foveal fixation cluster -> accumulate dwell and update smoothed center (EWMA)
                self._accumulated_dwell_ms += delta_t
                self._consecutive_outlier_count = 0
                alpha = 0.15
                new_cu = (1.0 - alpha) * self._fixation_center[0] + alpha * u
                new_cv = (1.0 - alpha) * self._fixation_center[1] + alpha * v
                self._fixation_center = (new_cu, new_cv)
                is_fixating = True
            elif dist <= 1.4 * self.fixation_radius_px:
                # Soft boundary / micro-drift: retain accumulated dwell, update center slowly
                self._accumulated_dwell_ms += delta_t * 0.50
                alpha = 0.25
                new_cu = (1.0 - alpha) * self._fixation_center[0] + alpha * u
                new_cv = (1.0 - alpha) * self._fixation_center[1] + alpha * v
                self._fixation_center = (new_cu, new_cv)
                is_fixating = True
            else:
                # Genuine saccadic jump away (> 1.4x radius)
                self._consecutive_outlier_count += 1
                if self._consecutive_outlier_count >= 2:
                    self._fixation_center = (u, v)
                    self._fixation_start_ms = timestamp_ms
                    self._accumulated_dwell_ms = 0.0
                    self._consecutive_outlier_count = 0
                    is_fixating = False
                else:
                    is_fixating = True

        # 4. Determine anchor: only emit anchor if accumulated dwell >= threshold
        if self._accumulated_dwell_ms >= threshold and self._fixation_center is not None:
            anchor: Optional[Tuple[float, float]] = (
                float(self._fixation_center[0]),
                float(self._fixation_center[1])
            )
        else:
            anchor = None

        return GazeDwellMetrics(
            gaze_dwell_ms=self._accumulated_dwell_ms,
            gaze_stability=stability,
            gaze_anchor=anchor,
            is_fixating=is_fixating
        )


__all__ = ["GazeDwellTracker", "GazeDwellMetrics"]
