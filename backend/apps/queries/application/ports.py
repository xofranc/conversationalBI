"""Ports para transacciones, caché, espera y motores externos de consulta."""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any, Protocol

from apps.queries.domain.exceptions import (
    SQLSafetyViolation,
    UnsupportedStatisticalAnalysis,
)
from apps.dataset.domain.ports import DatasetMaterializer as QueryDatasetMaterializer

from .dtos import (
    AIQueryRequestDTO,
    AnalysisQueryRequestDTO,
    ChartSelectionDTO,
    EngineResultDTO,
    QueryCacheKeyDTO,
    QueryResponseDTO,
    SQLExecutionResultDTO,
    StatisticalCalculationRequestDTO,
    StatisticalCalculationResultDTO,
)


class QueryCache(Protocol):
    def get(self, key: QueryCacheKeyDTO) -> QueryResponseDTO | None: ...

    def set(self, key: QueryCacheKeyDTO, value: QueryResponseDTO) -> None: ...

    def acquire_lock(self, key: QueryCacheKeyDTO) -> bool: ...

    def release_lock(self, key: QueryCacheKeyDTO) -> None: ...


class AIQueryEngine(Protocol):
    def execute(self, request: AIQueryRequestDTO) -> EngineResultDTO: ...


class AIPromptComposer(Protocol):
    """Compone prompts iniciales y de recuperación para una consulta AI."""

    def compose(self, request: AIQueryRequestDTO) -> str: ...

    def build_correction(
        self, question: str, schema: dict[str, Any], previous_sql: str, error: str
    ) -> str: ...

    def build_empty_result(
        self, question: str, schema: dict[str, Any], previous_sql: str
    ) -> str: ...


class SQLQueryGenerator(Protocol):
    """Genera SQL a partir de un prompt ya compuesto."""

    def generate(self, prompt: str) -> str: ...


class SQLSafetyValidator(Protocol):
    """Valida SQL y señala rechazos no reintentables con SQLSafetyViolation."""

    def validate(self, sql: str) -> None: ...


class SQLQueryExecutor(Protocol):
    """Ejecuta SQL en el dataset indicado sin exponer detalles de infraestructura."""

    def execute(self, dataset_id: int, sql: str) -> SQLExecutionResultDTO: ...


class AIChartSelector(Protocol):
    """Selecciona el tipo y la configuración visual de un resultado."""

    def select(
        self,
        columns: tuple[dict[str, Any], ...],
        rows: tuple[dict[str, Any], ...],
    ) -> ChartSelectionDTO: ...


class AIAnswerWriter(Protocol):
    """Redacta una respuesta de usuario a partir del resultado de SQL."""

    def write(
        self,
        question: str,
        sql: str,
        rows: tuple[dict[str, Any], ...],
        row_count: int,
    ) -> str: ...


class QuerySuggestionProvider(Protocol):
    """Propone preguntas alternativas para una consulta sin éxito."""

    def suggest(self, schema: dict[str, Any]) -> tuple[str, ...]: ...


class StatisticalAnalysisEngine(Protocol):
    def execute(self, request: AnalysisQueryRequestDTO) -> EngineResultDTO: ...


class StatisticalAnalysisCalculator(Protocol):
    """Calcula el resultado estadístico usando los datos del dataset indicado."""

    def calculate(
        self, request: StatisticalCalculationRequestDTO
    ) -> StatisticalCalculationResultDTO: ...


class StatisticalAnalysisAnswerWriter(Protocol):
    """Redacta una respuesta a partir del resultado de un análisis estadístico."""

    def write(
        self,
        question: str,
        method_comment: str,
        rows: tuple[dict[str, Any], ...],
        row_count: int,
    ) -> str: ...


class QueryTransaction(Protocol):
    def atomic(self) -> AbstractContextManager[None]: ...


class Waiter(Protocol):
    def sleep(self, seconds: float) -> None: ...
