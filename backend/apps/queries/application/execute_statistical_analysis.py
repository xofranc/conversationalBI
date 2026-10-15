"""Orquesta el cálculo y la respuesta de un análisis estadístico."""

from __future__ import annotations

import time

from .dtos import (
    AnalysisQueryRequestDTO,
    EngineResultDTO,
    StatisticalCalculationRequestDTO,
)
from .ports import (
    QuerySuggestionProvider,
    StatisticalAnalysisAnswerWriter,
    StatisticalAnalysisCalculator,
    StatisticalAnalysisEngine,
    UnsupportedStatisticalAnalysis,
)


class ExecuteStatisticalAnalysis(StatisticalAnalysisEngine):
    """Implementa el port del motor combinando cálculo, respuesta y sugerencias."""

    UNEXPECTED_FAILURE_MESSAGE = (
        "El análisis falló de forma inesperada. Intenta con otra pregunta."
    )

    def __init__(
        self,
        calculator: StatisticalAnalysisCalculator,
        answers: StatisticalAnalysisAnswerWriter,
        suggestions: QuerySuggestionProvider,
    ) -> None:
        self._calculator = calculator
        self._answers = answers
        self._suggestions = suggestions

    def execute(self, request: AnalysisQueryRequestDTO) -> EngineResultDTO:
        started_at = time.perf_counter()
        model_used = f"análisis:{request.intent}"

        try:
            calculation = self._calculator.calculate(
                StatisticalCalculationRequestDTO(
                    intent=request.intent,
                    dataset_id=request.dataset_id,
                    question=request.question,
                )
            )
        except UnsupportedStatisticalAnalysis as exc:
            return self._failed_result(
                request,
                error_message=str(exc),
                model_used=model_used,
                started_at=started_at,
            )
        except Exception:
            return self._failed_result(
                request,
                error_message=self.UNEXPECTED_FAILURE_MESSAGE,
                model_used=model_used,
                started_at=started_at,
            )

        method_comment = f"-- {calculation.method}"
        answer = self._answers.write(
            request.question,
            method_comment,
            calculation.rows,
            len(calculation.rows),
        )
        return EngineResultDTO(
            sql=method_comment,
            success=True,
            execution_time=round(time.perf_counter() - started_at, 3),
            rows=calculation.rows,
            columns=calculation.columns,
            chart_type=calculation.chart_type,
            chart_config=calculation.chart_config,
            answer=answer,
            model_used=model_used,
        )

    def _failed_result(
        self,
        request: AnalysisQueryRequestDTO,
        *,
        error_message: str,
        model_used: str,
        started_at: float,
    ) -> EngineResultDTO:
        return EngineResultDTO(
            success=False,
            error_message=error_message,
            execution_time=round(time.perf_counter() - started_at, 3),
            chart_type="table",
            chart_config={},
            suggestions=self._suggestions.suggest(request.schema),
            model_used=model_used,
        )
