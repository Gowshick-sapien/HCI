"""
Layer 5: Dual-Scale Dynamic Adaptation & Runtime Assessment Package.
Provides closed-loop performance assessment, SPRT gatekeeper validation,
online micro-adaptation on the probability simplex, and macro-adaptation policy management.
"""

from src.adaptation.assessment_engine import AssessmentEngine
from src.adaptation.coordinator import AdaptationCoordinator
from src.adaptation.gatekeeper import Gatekeeper
from src.adaptation.macro_adaptation import MacroAdaptationEngine
from src.adaptation.micro_adaptation import MicroAdaptationEngine, project_to_simplex_with_min
from src.storage.schemas import (
    AssessmentMetrics,
    GatekeeperDecision,
    GatekeeperVerdict,
    MacroPolicy,
    SystemHealthState,
)

__all__ = [
    "AssessmentEngine",
    "AdaptationCoordinator",
    "Gatekeeper",
    "MicroAdaptationEngine",
    "MacroAdaptationEngine",
    "project_to_simplex_with_min",
    "AssessmentMetrics",
    "GatekeeperDecision",
    "GatekeeperVerdict",
    "MacroPolicy",
    "SystemHealthState",
]
