"""Adaptadores concretos para el caso de uso de análisis estadístico."""

from __future__ import annotations

from typing import Any

from apps.dataset.infrastructure.query_data_source import DatasetQueryDataSource
from apps.queries.application.dtos import (
    StatisticalCalculationRequestDTO,
    StatisticalCalculationResultDTO,
)
from apps.queries.application.ports import UnsupportedStatisticalAnalysis
from apps.queries.domain.policies import AnalysisLimits
from apps.queries.infrastructure.ai.answer_writer import AnswerWriter

from . import engine


class PandasStatisticalAnalysisCalculator:
    """Carga datos por el data source y delega el cálculo al motor pandas."""

    def __init__(self, data_source: DatasetQueryDataSource) -> None:
        self._data_source = data_source
        self._limits = AnalysisLimits()

    def calculate(
        self, request: StatisticalCalculationRequestDTO
    ) -> StatisticalCalculationResultDTO:
        dataset = self._data_source.get_dataset(request.dataset_id)
        tables = self._data_source.read_tables(dataset)
        try:
            result = engine.run(
                request.intent,
                tables,
                request.question,
                infer_dtype=self._data_source.infer_dtype,
                limits=self._limits,
            )
        except engine.AnalysisError as exc:
            raise UnsupportedStatisticalAnalysis(str(exc)) from exc

        return StatisticalCalculationResultDTO(
            method=result["method"],
            rows=tuple(result["rows"]),
            columns=tuple(result["columns"]),
            chart_type=result["chart_type"],
            chart_config=result["chart_config"],
        )


class StatisticalAnalysisAnswerWriterAdapter:
    """Adapta AnswerWriter al port de respuesta estadística de application."""

    def __init__(self, writer: AnswerWriter | None = None) -> None:
        self._writer = writer or AnswerWriter()

    def write(
        self,
        question: str,
        method_comment: str,
        rows: tuple[dict[str, Any], ...],
        row_count: int,
    ) -> str:
        return self._writer.write(question, method_comment, list(rows), row_count)
