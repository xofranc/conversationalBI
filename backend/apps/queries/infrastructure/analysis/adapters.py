"""Adaptadores concretos para el caso de uso de análisis estadístico."""

from __future__ import annotations

from typing import Any

from apps.dataset.domain.ports import DatasetDataReader
from apps.queries.domain.exceptions import UnsupportedStatisticalAnalysis
from apps.queries.domain.policies import AnalysisLimits
from apps.queries.domain.value_objects import StatisticalCalculationResult

from . import engine


class PandasStatisticalAnalysisCalculator:
    """Carga datos por el data source y delega el cálculo al motor pandas."""

    def __init__(self, data_source: DatasetDataReader) -> None:
        self._data_source = data_source
        self._limits = AnalysisLimits()

    def calculate(
        self, request: Any
    ) -> StatisticalCalculationResult:
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

        return StatisticalCalculationResult(
            method=result["method"],
            rows=tuple(result["rows"]),
            columns=tuple(result["columns"]),
            chart_type=result["chart_type"],
            chart_config=result["chart_config"],
        )
