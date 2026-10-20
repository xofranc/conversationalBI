"""Compatibility bridge to the application AI query use case."""


class AIQueryService:
    """Keep the legacy dict API while delegating orchestration to application."""

    @staticmethod
    def execute(
        question: str,
        dataset_id: int,
        schema: dict,
        history: list | None = None,
        *,
        data_source,
    ) -> dict:
        from apps.queries.application.dtos import AIQueryRequestDTO, ConversationTurnDTO
        from config.composition import build_ai_query_engine

        request = AIQueryRequestDTO(
            question=question,
            dataset_id=dataset_id,
            schema=schema,
            history=tuple(
                ConversationTurnDTO(question=turn["question"], sql=turn["sql"])
                for turn in (history or ())
            ),
        )
        result = build_ai_query_engine(data_source=data_source).execute(request)
        return {
            "sql": result.sql,
            "success": result.success,
            "error_msg": result.error_message,
            "retry_count": result.retry_count,
            "execution_time": result.execution_time,
            "rows": list(result.rows),
            "columns": list(result.columns),
            "chart_type": result.chart_type,
            "chart_config": result.chart_config or {},
            "answer": result.answer,
            "suggestions": list(result.suggestions),
        }
