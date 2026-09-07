"""
Evaluation & Benchmarking Subsystem (Deliverable E3).
Latin Square counterbalanced A/B test coordinator, task automation, and statistical testing suite.
"""

from src.evaluation.statistical_analyzer import (
    ConditionStatistics,
    StatisticalAnalyzer,
    StatisticalComparison,
)
from src.evaluation.study_manager import (
    ExperimentalCondition,
    StudyManager,
    TrialResult,
    TrialTarget,
)

__all__ = [
    "ConditionStatistics",
    "ExperimentalCondition",
    "StatisticalAnalyzer",
    "StatisticalComparison",
    "StudyManager",
    "TrialResult",
    "TrialTarget",
]
