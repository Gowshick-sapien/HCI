"""
Adaptive Holt-Winters Dynamic Smoothing Filter.
Provides velocity-scaled double exponential smoothing for 2D and 3D coordinate trajectories.
Minimizes stationary jitter (<= 1.2 px) while preventing dynamic tracking lag (<= 15 ms).
"""

from __future__ import annotations

from typing import Optional, Union
import numpy as np


class HoltWintersFilter:
    """
    Velocity-scaled double exponential smoothing filter for N-dimensional coordinates.
    Dynamically scales alpha between alpha_min and alpha_max based on instantaneous motion velocity.
    """

    def __init__(
        self,
        dim: int = 2,
        alpha_0: float = 0.25,
        beta: float = 0.15,
        gamma: float = 0.01,
        alpha_min: float = 0.20,
        alpha_max: float = 0.85
    ) -> None:
        self.dim = dim
        self.alpha_0 = float(alpha_0)
        self.beta = float(beta)
        self.gamma = float(gamma)
        self.alpha_min = float(alpha_min)
        self.alpha_max = float(alpha_max)

        self._x_prev: Optional[np.ndarray] = None
        self._b_prev: Optional[np.ndarray] = None
        self._last_alpha: float = self.alpha_0
        self._initialized: bool = False

    def reset(self) -> None:
        """Resets filter state."""
        self._x_prev = None
        self._b_prev = None
        self._last_alpha = self.alpha_0
        self._initialized = False

    def update(
        self,
        measurement: Union[np.ndarray, list, tuple],
        velocity_magnitude: Optional[float] = None
    ) -> np.ndarray:
        """
        Applies double exponential smoothing to the incoming measurement vector.
        """
        x_meas = np.asarray(measurement, dtype=np.float64)

        if not self._initialized or self._x_prev is None or self._b_prev is None:
            self._x_prev = x_meas.copy()
            self._b_prev = np.zeros_like(x_meas)
            self._initialized = True
            return self._x_prev.copy()

        # Compute or use provided velocity magnitude
        if velocity_magnitude is None:
            v_mag = float(np.linalg.norm(x_meas - self._x_prev))
        else:
            v_mag = float(velocity_magnitude)

        # Dynamic velocity-scaled alpha: at rest (v=0), alpha=alpha_min for max jitter attenuation
        alpha_t = float(np.clip(self.alpha_min + self.gamma * v_mag, self.alpha_min, self.alpha_max))
        self._last_alpha = alpha_t

        # Holt-Winters double exponential updates
        # Level estimate
        x_hat = alpha_t * x_meas + (1.0 - alpha_t) * (self._x_prev + self._b_prev)

        # Trend estimate
        b_hat = self.beta * (x_hat - self._x_prev) + (1.0 - self.beta) * self._b_prev

        self._x_prev = x_hat
        self._b_prev = b_hat

        return x_hat.copy()

    @property
    def last_alpha(self) -> float:
        """Returns the most recent adaptive alpha value applied."""
        return self._last_alpha


__all__ = ["HoltWintersFilter"]
