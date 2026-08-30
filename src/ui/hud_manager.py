"""
UI Subsystem: Master Explainability HUD Manager Facade.
Coordinates perception, fusion, feedback, and adaptation data streams with the non-blocking HUD overlay.
"""

from __future__ import annotations

import logging
import threading
from typing import Dict, Optional

from src.storage.schemas import (
    AssessmentMetrics,
    ComposedCommand,
    DeviceMode,
    FeedbackEvent,
    PerceptionFrame,
)
from src.ui.explainability_hud import ExplainabilityHUDOverlay

logger = logging.getLogger(__name__)


class HUDManager:
    """
    Master coordinator facade for the Explainability HUD.
    Receives pipeline telemetry across multiple threads and pushes synchronized updates to the HUD overlay.
    """

    def __init__(
        self,
        screen_width: int = 1920,
        screen_height: int = 1080,
        target_fps: int = 60,
        enable_overlay: bool = True
    ) -> None:
        self.screen_width = int(screen_width)
        self.screen_height = int(screen_height)
        self.target_fps = int(target_fps)
        self.enable_overlay = bool(enable_overlay)

        self._lock = threading.RLock()
        self._overlay_window: Optional[ExplainabilityHUDOverlay] = None

    def initialize_overlay(self) -> Optional[ExplainabilityHUDOverlay]:
        """Initializes and shows the translucent PySide6 overlay window."""
        if not self.enable_overlay:
            return None

        with self._lock:
            if self._overlay_window is None:
                self._overlay_window = ExplainabilityHUDOverlay(
                    screen_width=self.screen_width,
                    screen_height=self.screen_height,
                    target_fps=self.target_fps
                )
                self._overlay_window.show()
                logger.info("ExplainabilityHUDOverlay initialized and active.")
            return self._overlay_window

    def update_frame(
        self,
        perception: Optional[PerceptionFrame] = None,
        command: Optional[ComposedCommand] = None,
        metrics: Optional[AssessmentMetrics] = None,
        feedback: Optional[FeedbackEvent] = None,
        device_mode: Optional[DeviceMode] = None,
        weights: Optional[Dict[str, float]] = None
    ) -> None:
        """Pushes telemetry updates to the overlay window under lock."""
        with self._lock:
            if self._overlay_window is not None:
                self._overlay_window.update_telemetry(
                    perception=perception,
                    command=command,
                    metrics=metrics,
                    feedback=feedback,
                    device_mode=device_mode,
                    weights=weights
                )

    def close(self) -> None:
        """Closes the overlay window."""
        with self._lock:
            if self._overlay_window is not None:
                self._overlay_window.close()
                self._overlay_window = None


__all__ = ["HUDManager"]
