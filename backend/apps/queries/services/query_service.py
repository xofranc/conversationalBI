"""Compatibility facade for the application query use case."""

from apps.queries.application.dtos import ExecuteQueryInput


def _execute_query_use_case():
    # Imported lazily to avoid initializing Django adapters during module import.
    from config.composition import build_query_use_cases

    return build_query_use_cases()["execute"]


class QueryService:
    @staticmethod
    def execute(question: str, dataset_id: int, user) -> dict:
        result = _execute_query_use_case().execute(ExecuteQueryInput(
            user_id=user.pk,
            dataset_id=dataset_id,
            question=question,
        ))
        response = {
            "query_id": result.query_id,
            "sql": result.sql,
            "success": result.success,
            "error_msg": result.error_message,
            "execution_time": result.execution_time,
            "model_used": result.model_used,
            "retry_count": result.retry_count,
            "cached": result.cached,
            "data": list(result.data),
            "columns": list(result.columns),
            "chart_type": result.chart_type,
            "chart_config": result.chart_config,
            "row_count": result.row_count,
            "answer": result.answer,
        }
        if not result.success:
            response["suggestions"] = list(result.suggestions)
        return response
