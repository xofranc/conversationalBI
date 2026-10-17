"""Dominio de historial, resultados, feedback y políticas deterministas."""

from .entities import QueryFeedback, QueryHistory, QueryResult
from .exceptions import (
    DomainError,
    InvalidFeedbackScore,
    InvalidPolicyConfiguration,
    SQLSafetyViolation,
    UnsupportedStatisticalAnalysis,
)
from .policies import (
    AnalysisIntent,
    AnalysisIntentPolicy,
    AnalysisLimits,
    QueryExecutionPolicy,
    SQLSafetyPolicy,
)
from .value_objects import (
    ChartSelection,
    ChartType,
    FeedbackScore,
    SQLExecutionResult,
    StatisticalCalculationResult,
)

__all__ = [
    "AnalysisIntent",
    "AnalysisIntentPolicy",
    "AnalysisLimits",
    "ChartSelection",
    "ChartType",
    "DomainError",
    "FeedbackScore",
    "InvalidFeedbackScore",
    "InvalidPolicyConfiguration",
    "QueryExecutionPolicy",
    "QueryFeedback",
    "QueryHistory",
    "QueryResult",
    "SQLExecutionResult",
    "SQLSafetyViolation",
    "SQLSafetyPolicy",
    "StatisticalCalculationResult",
    "UnsupportedStatisticalAnalysis",
]
