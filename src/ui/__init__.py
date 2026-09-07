"""
UI & Visualization Subsystem (Deliverables E2 & E3).
State-aware explainability HUD overlay, visual dwell confirmation rings, and empirical research dashboard.
"""

from src.ui.confidence_bars import ConfidenceBarsRenderer
from src.ui.dwell_confirmation_ring import DwellConfirmationRing
from src.ui.explainability_hud import ExplainabilityHUDOverlay
from src.ui.health_badge_renderer import HealthBadgeRenderer
from src.ui.hud_manager import HUDManager
from src.ui.latin_square_panel import LatinSquarePanel
from src.ui.parameter_evolution_plot import ParameterEvolutionCanvas, ParameterEvolutionPlot
from src.ui.research_dashboard import ResearchDashboardWindow
from src.ui.sprt_trajectory_gauge import SPRTTrajectoryCanvas, SPRTTrajectoryGauge
from src.ui.telemetry_stream_viewer import TelemetryStreamViewer, TelemetryTableModel

__all__ = [
    "ConfidenceBarsRenderer",
    "DwellConfirmationRing",
    "ExplainabilityHUDOverlay",
    "HealthBadgeRenderer",
    "HUDManager",
    "LatinSquarePanel",
    "ParameterEvolutionCanvas",
    "ParameterEvolutionPlot",
    "ResearchDashboardWindow",
    "SPRTTrajectoryCanvas",
    "SPRTTrajectoryGauge",
    "TelemetryStreamViewer",
    "TelemetryTableModel",
]
