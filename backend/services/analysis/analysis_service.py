"""Shim de compatibilidad para la API legacy de análisis."""

class AnalysisService:
    @staticmethod
    def execute(
        analysis_type: str,
        dataset_id: int,
        question: str,
        *,
        analysis_engine,
        schema: dict,
    ) -> dict:
        from apps.queries.application.dtos import AnalysisQueryRequestDTO

        result = analysis_engine.execute(
            AnalysisQueryRequestDTO(
                intent=analysis_type,
                dataset_id=dataset_id,
                question=question,
                schema=schema,
            )
        )
        model_labels = {
            "forecast": "análisis:pronóstico",
            "anomaly": "análisis:anomalías",
            "segment": "análisis:segmentación",
            "drivers": "análisis:factores",
            "summary": "análisis:resumen",
        }
        return {
            "sql": result.sql,
            "model_used": model_labels.get(
                analysis_type, f"análisis:{analysis_type}"
            ),
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
