"""Contratos de persistencia para consulta, resultado y feedback."""

from __future__ import annotations

from typing import Protocol, Sequence

from .entities import QueryFeedback, QueryHistory, QueryResult


class QueryHistoryRepository(Protocol):
    def get_by_id(self, query_id: int) -> QueryHistory | None: ...

    def list_by_user(self, user_id: int) -> Sequence[QueryHistory]: ...

    def list_by_dataset(self, dataset_id: int) -> Sequence[QueryHistory]: ...

    def save(self, query: QueryHistory) -> QueryHistory: ...


class QueryResultRepository(Protocol):
    """QueryResult tiene cardinalidad uno-a-uno con QueryHistory."""

    def get_by_query_id(self, query_id: int) -> QueryResult | None: ...

    def save(self, result: QueryResult) -> QueryResult: ...


class QueryFeedbackRepository(Protocol):
    """QueryFeedback tiene cardinalidad uno-a-uno con QueryHistory."""

    def get_by_query_id(self, query_id: int) -> QueryFeedback | None: ...

    def save(self, feedback: QueryFeedback) -> QueryFeedback: ...
