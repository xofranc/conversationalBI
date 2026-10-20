"""Orquesta la generación y ejecución de una consulta asistida por AI."""

from __future__ import annotations

import time
from typing import Any

from apps.queries.domain.policies import QueryExecutionPolicy, SQLSafetyPolicy

from .dtos import AIQueryRequestDTO, EngineResultDTO
from .ports import (
    AIAnswerWriter,
    AIChartSelector,
    AIQueryEngine,
    AIPromptComposer,
    QuerySuggestionProvider,
    SQLQueryExecutor,
    SQLQueryGenerator,
    SQLSafetyValidator,
    SQLSafetyViolation,
)


class _EmptyResult(Exception):
    """Un SQL válido sin filas que debe reintentarse con pistas del esquema."""


class GenerateAIQuery(AIQueryEngine):
    """Implementación de aplicación del port ``AIQueryEngine``.

    Las capacidades de prompts, generación, validación, ejecución y respuesta
    se reciben por inyección; esta clase solo define el flujo y sus reintentos.
    """

    NO_SQL_POSSIBLE_MESSAGE = "Esa pregunta no se puede responder con las columnas de esta fuente."
    EMPTY_RESULT_MESSAGE = "La consulta devolvió 0 filas."

    def __init__(
        self,
        prompts: AIPromptComposer,
        generator: SQLQueryGenerator,
        safety: SQLSafetyValidator,
        executor: SQLQueryExecutor,
        charts: AIChartSelector,
        answers: AIAnswerWriter,
        suggestions: QuerySuggestionProvider,
        safety_policy: SQLSafetyPolicy = SQLSafetyPolicy(),
    ) -> None:
        self._prompts = prompts
        self._generator = generator
        self._safety = safety
        self._executor = executor
        self._charts = charts
        self._answers = answers
        self._suggestions = suggestions
        self._safety_policy = safety_policy
        self._policy = QueryExecutionPolicy()

    def execute(self, request: AIQueryRequestDTO) -> EngineResultDTO:
        """Genera SQL, lo valida y ejecuta, reintentando fallos recuperables."""
        prompt = self._prompts.compose(request)
        sql = ""
        error_message = ""
        retry_count = 0
        success = False
        rows: tuple[dict[str, Any], ...] = ()
        columns: tuple[dict[str, Any], ...] = ()
        start = time.time()

        for attempt in range(self._policy.max_attempts):
            try:
                sql = self._generator.generate(prompt)

                if sql.strip().startswith("NO_SQL_POSSIBLE"):
                    error_message = self.NO_SQL_POSSIBLE_MESSAGE
                    break

                self._safety.validate(sql)
                execution = self._executor.execute(request.dataset_id, sql)
                rows, columns = execution.rows, execution.columns

                if not rows and attempt < self._policy.max_attempts - 1:
                    raise _EmptyResult(self.EMPTY_RESULT_MESSAGE)

                success = True
                retry_count = attempt
                break

            except SQLSafetyViolation as exc:
                error_message = str(exc)
                retry_count = attempt
                if (
                    not self._safety_policy.security_rejection_is_retryable
                    or attempt >= self._policy.max_attempts - 1
                ):
                    break

                retry_count = attempt + 1
                prompt = self._prompts.build_correction(
                    question=request.question,
                    schema=request.schema,
                    previous_sql=sql,
                    error=error_message,
                )

            except _EmptyResult as exc:
                error_message = str(exc)
                retry_count = attempt + 1
                prompt = self._prompts.build_empty_result(
                    question=request.question,
                    schema=request.schema,
                    previous_sql=sql,
                )

            except Exception as exc:
                error_message = str(exc)
                retry_count = attempt + 1
                prompt = self._prompts.build_correction(
                    question=request.question,
                    schema=request.schema,
                    previous_sql=sql,
                    error=error_message,
                )

        if success:
            selection = self._charts.select(columns, rows)
            answer = self._answers.write(request.question, sql, rows, len(rows))
            query_suggestions: tuple[str, ...] = ()
            chart_type = selection.chart_type
            chart_config = selection.chart_config
        else:
            answer = ""
            query_suggestions = self._suggestions.suggest(request.schema)
            chart_type = "table"
            chart_config = {}

        return EngineResultDTO(
            sql=sql,
            success=success,
            error_message=error_message,
            retry_count=retry_count,
            execution_time=round(time.time() - start, 3),
            rows=rows,
            columns=columns,
            chart_type=chart_type,
            chart_config=chart_config,
            answer=answer,
            suggestions=query_suggestions,
        )
