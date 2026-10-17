"""DTOs para ejecución, caché, historial y feedback de consultas."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from apps.queries.domain.value_objects import (
    ChartSelection as ChartSelectionDTO,
    SQLExecutionResult as SQLExecutionResultDTO,
    StatisticalCalculationResult as StatisticalCalculationResultDTO,
)


@dataclass(frozen=True)
class ExecuteQueryInput:
    user_id: int
    dataset_id: int
    question: str


@dataclass(frozen=True)
class ConversationTurnDTO:
    question: str
    sql: str


@dataclass(frozen=True)
class AIQueryRequestDTO:
    question: str
    dataset_id: int
    schema: dict[str, Any]
    history: tuple[ConversationTurnDTO, ...]


@dataclass(frozen=True)
class AnalysisQueryRequestDTO:
    intent: str
    dataset_id: int
    question: str
    schema: dict[str, Any]


@dataclass(frozen=True)
class StatisticalCalculationRequestDTO:
    """Entrada del cálculo estadístico, sin detalles de almacenamiento."""

    intent: str
    dataset_id: int
    question: str


@dataclass(frozen=True)
class EngineResultDTO:
    sql: str = ""
    success: bool = False
    error_message: str = ""
    retry_count: int = 0
    execution_time: float = 0.0
    rows: tuple[dict[str, Any], ...] = ()
    columns: tuple[dict[str, Any], ...] = ()
    chart_type: str = "table"
    chart_config: dict[str, Any] | None = None
    answer: str = ""
    suggestions: tuple[str, ...] = ()
    model_used: str = ""


@dataclass(frozen=True)
class QueryCacheKeyDTO:
    question: str
    dataset_id: int
    dataset_version: str


@dataclass(frozen=True)
class QueryResponseDTO:
    query_id: int | None
    sql: str
    success: bool
    error_message: str
    execution_time: float
    model_used: str
    retry_count: int
    cached: bool
    data: tuple[dict[str, Any], ...]
    columns: tuple[dict[str, Any], ...]
    chart_type: str
    chart_config: dict[str, Any]
    row_count: int
    answer: str
    suggestions: tuple[str, ...] = ()


@dataclass(frozen=True)
class ListQueryHistoryInput:
    user_id: int
    dataset_id: int | None = None


@dataclass(frozen=True)
class GetQueryDetailInput:
    user_id: int
    query_id: int


@dataclass(frozen=True)
class QueryHistoryItemDTO:
    query_id: int | None
    question: str
    success: bool
    execution_time: float
    model_used: str
    retry_count: int
    cached: bool
    created_at: datetime | None


@dataclass(frozen=True)
class QueryResultDTO:
    data: tuple[dict[str, Any], ...]
    columns: tuple[dict[str, Any], ...]
    row_count: int
    chart_type: str
    chart_config: dict[str, Any]
    answer: str


@dataclass(frozen=True)
class QueryDetailDTO:
    query_id: int | None
    question: str
    sql: str
    execution_time: float
    success: bool
    error_message: str
    model_used: str
    retry_count: int
    cached: bool
    created_at: datetime | None
    result: QueryResultDTO | None


@dataclass(frozen=True)
class SubmitFeedbackInput:
    user_id: int
    query_id: int
    score: int
    comment: str = ""


@dataclass(frozen=True)
class FeedbackDTO:
    query_id: int
    score: int
    comment: str
    created_at: datetime | None
