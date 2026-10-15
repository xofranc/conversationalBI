"""Entidades inmutables de historial de consulta, resultado y feedback."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .value_objects import ChartType, FeedbackScore


@dataclass(frozen=True)
class QueryHistory:
    user_id: int
    dataset_id: int
    question: str
    sql_generated: str = ""
    execution_time: float = 0.0
    success: bool = False
    error_msg: str = ""
    model_used: str = ""
    retry_count: int = 0
    cached: bool = False
    created_at: datetime | None = None
    id: int | None = None


@dataclass(frozen=True)
class QueryResult:
    """Relación uno-a-uno con QueryHistory."""

    query_id: int
    result_json: list[dict[str, Any]] = field(default_factory=list)
    columns: list[dict[str, Any]] = field(default_factory=list)
    row_count: int = 0
    answer: str = ""
    chart_type: ChartType = ChartType.TABLE
    chart_config: dict[str, Any] = field(default_factory=dict)
    id: int | None = None


@dataclass(frozen=True)
class QueryFeedback:
    """Feedback uno-a-uno con QueryHistory."""

    query_id: int
    score: FeedbackScore
    comment: str = ""
    created_at: datetime | None = None
    id: int | None = None
