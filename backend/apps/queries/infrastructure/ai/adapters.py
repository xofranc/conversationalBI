"""Adaptadores concretos de infraestructura para los puertos AI de application."""

from __future__ import annotations

from typing import Any

from apps.queries.application.dtos import (
    AIQueryRequestDTO,
    ChartSelectionDTO,
    SQLExecutionResultDTO,
)
from apps.queries.application.ports import SQLSafetyViolation
from apps.queries.domain.policies import QueryExecutionPolicy, SQLSafetyPolicy

from .answer_writer import AnswerWriter
from .chart_selector import ChartSelector
from .prompt_builder import PromptBuilder
from .sql_agent import SQLAgent
from .sql_executor import SQLExecutor
from .sql_validator import SQLValidator, SecurityError
from .suggester import suggest


class AIPromptComposerAdapter:
    def compose(self, request: AIQueryRequestDTO) -> str:
        history = [{"question": turn.question, "sql": turn.sql} for turn in request.history]
        return PromptBuilder.build(request.question, request.schema, history)

    def build_correction(self, question: str, schema: dict[str, Any], previous_sql: str, error: str) -> str:
        return PromptBuilder.build_correction(question, schema, previous_sql, error)

    def build_empty_result(self, question: str, schema: dict[str, Any], previous_sql: str) -> str:
        return PromptBuilder.build_empty_result(question, schema, previous_sql)


class SQLQueryGeneratorAdapter:
    def __init__(self, agent: SQLAgent | None = None):
        self._agent = agent or SQLAgent()

    def generate(self, prompt: str) -> str:
        return self._agent.run(prompt)


class SQLSafetyValidatorAdapter:
    def __init__(self, policy: SQLSafetyPolicy | None = None):
        self._validator = SQLValidator(policy or SQLSafetyPolicy())

    def validate(self, sql: str) -> None:
        try:
            self._validator.assert_safe(sql)
        except SecurityError as exc:
            raise SQLSafetyViolation(str(exc)) from exc


class DatasetSQLQueryExecutor:
    def __init__(self, data_source, policy: QueryExecutionPolicy | None = None):
        self._executor = SQLExecutor(data_source, policy or QueryExecutionPolicy())

    def execute(self, dataset_id: int, sql: str) -> SQLExecutionResultDTO:
        rows, columns = self._executor.run(sql, dataset_id)
        return SQLExecutionResultDTO(rows=tuple(rows), columns=tuple(columns))


class AIChartSelectorAdapter:
    def select(
        self,
        columns: tuple[dict[str, Any], ...],
        rows: tuple[dict[str, Any], ...],
    ) -> ChartSelectionDTO:
        selection = ChartSelector.select(list(columns), list(rows))
        return ChartSelectionDTO(
            chart_type=selection["chart_type"],
            chart_config=selection["chart_config"],
        )


class AIAnswerWriterAdapter:
    def __init__(self, writer: AnswerWriter | None = None):
        self._writer = writer or AnswerWriter()

    def write(self, question: str, sql: str, rows: tuple[dict[str, Any], ...], row_count: int) -> str:
        return self._writer.write(question, sql, list(rows), row_count)


class QuerySuggestionAdapter:
    def suggest(self, schema: dict[str, Any]) -> tuple[str, ...]:
        return tuple(suggest(schema))
