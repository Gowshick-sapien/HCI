"""
Casiez et al. (CHI 2012) 1-Euro Filter.
Adaptive low-pass filter for latency-minimized jitter reduction in real-time HCI input.
"""

from __future__ import annotations

import math
from typing import Optional, Sequence, Union
import numpy as np


class LowPassFilter:
    """Standard first-order exponential low-pass filter."""

    def __init__(self, alpha: Union[float, np.ndarray] = 1.0, init_val: Optional[np.ndarray] = None) -> None:
        self.alpha = alpha
        self.y: Optional[np.ndarray] = None if init_val is None else np.asarray(init_val, dtype=np.float64)

    def filter(self, value: np.ndarray, alpha: Optional[Union[float, np.ndarray]] = None) -> np.ndarray:
        if alpha is not None:
            self.alpha = alpha
        if self.y is None:
            self.y = np.asarray(value, dtype=np.float64).copy()
        else:
            self.y = self.alpha * np.asarray(value, dtype=np.float64) + (1.0 - self.alpha) * self.y
        return self.y

    def reset(self, init_val: Optional[np.ndarray] = None) -> None:
        self.y = None if init_val is None else np.asarray(init_val, dtype=np.float64).copy()


class OneEuroFilter:
    """
    1-Euro adaptive smoothing filter for N-dimensional vectors or scalar inputs.
    Dynamically increases cutoff frequency as speed increases to reduce lag during saccades,
    while keeping cutoff minimal at rest to eliminate jitter.
    """

    def __init__(
        self,
        fc_min: float = 0.8,
        beta: float = 0.007,
        d_cutoff: float = 1.0,
        dim: int = 2,
    ) -> None:
        self.fc_min = float(fc_min)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)
        self.dim = int(dim)

        self._x_filter = LowPassFilter()
        self._dx_filter = LowPassFilter()
        self._last_time: Optional[float] = None

    @staticmethod
    def _compute_alpha(rate: float, cutoff: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        tau = 1.0 / (2.0 * math.pi * cutoff)
        te = 1.0 / rate
        return 1.0 / (1.0 + tau / te)

    def update(
        self,
        value: Union[float, Sequence[float], np.ndarray],
        timestamp_sec: Optional[float] = None,
    ) -> np.ndarray:
        val = np.asarray(value, dtype=np.float64)
        if timestamp_sec is None:
            return val

        t = float(timestamp_sec)

        if self._last_time is None or self._x_filter.y is None:
            self._last_time = t
            self._x_filter.reset(val)
            self._dx_filter.reset(np.zeros_like(val))
            return val

        dt = t - self._last_time
        if dt <= 1e-6:
            # Avoid division by zero on duplicate or invalid timestamps
            return self._x_filter.y.copy()

        self._last_time = t
        rate = 1.0 / dt

        # 1. Estimate and filter derivative
        prev_x = self._x_filter.y
        dx = (val - prev_x) * rate
        alpha_d = self._compute_alpha(rate, self.d_cutoff)
        filtered_dx = self._dx_filter.filter(dx, alpha=alpha_d)

        # 2. Compute adaptive cutoff frequency per dimension
        speed = np.abs(filtered_dx)
        fc = self.fc_min + self.beta * speed

        # 3. Filter the signal with adaptive alpha
        alpha = self._compute_alpha(rate, fc)
        return self._x_filter.filter(val, alpha=alpha)

    def reset(self) -> None:
        """Reset internal filter states."""
        self._x_filter.reset()
        self._dx_filter.reset()
        self._last_time = None


__all__ = ["OneEuroFilter"]
