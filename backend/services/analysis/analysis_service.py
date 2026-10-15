"""Shim de compatibilidad para la API legacy de análisis."""

from apps.queries.infrastructure.composition import (
    execute_legacy_statistical_analysis,
)


class AnalysisService:
    @staticmethod
    def execute(
        analysis_type: str,
        dataset_id: int,
        question: str,
        *,
        data_source=None,
    ) -> dict:
        return execute_legacy_statistical_analysis(
            analysis_type,
            dataset_id,
            question,
            data_source=data_source,
        )
