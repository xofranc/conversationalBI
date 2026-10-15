"""Composition root para casos de uso de consultas."""

from django.conf import settings

from apps.dataset.infrastructure.query_data_source import DatasetQueryDataSource
from apps.dataset.infrastructure.repositories import DjangoDatasetRepository
from apps.queries.application.use_cases import (
    ExecuteQuery,
    GetQueryDetail,
    ListQueryHistory,
    SubmitQueryFeedback,
)
from apps.queries.application.generate_ai_query import GenerateAIQuery
from apps.queries.application.dtos import (
    AIQueryRequestDTO,
    AnalysisQueryRequestDTO,
    ConversationTurnDTO,
)
from apps.queries.application.execute_statistical_analysis import ExecuteStatisticalAnalysis
from apps.queries.domain.policies import QueryExecutionPolicy, SQLSafetyPolicy
from apps.users.infrastructure.repositories import DjangoProfileRepository

from .adapters import (
    DjangoQueryCache,
    DjangoQueryTransaction,
    QueryDatasetMaterializer,
    ThreadWaiter,
)
from .analysis import (
    PandasStatisticalAnalysisCalculator,
    StatisticalAnalysisAnswerWriterAdapter,
)
from .ai import (
    AIAnswerWriterAdapter,
    AIChartSelectorAdapter,
    AIPromptComposerAdapter,
    DatasetSQLQueryExecutor,
    QuerySuggestionAdapter,
    SQLQueryGeneratorAdapter,
    SQLSafetyValidatorAdapter,
)
from .repositories import (
    DjangoQueryFeedbackRepository,
    DjangoQueryHistoryRepository,
    DjangoQueryResultRepository,
)


def build_ai_query_engine(data_source) -> GenerateAIQuery:
    """Compone el caso de uso AI; los reintentos permanecen en application."""
    execution_policy = QueryExecutionPolicy()
    return GenerateAIQuery(
        prompts=AIPromptComposerAdapter(),
        generator=SQLQueryGeneratorAdapter(),
        safety=SQLSafetyValidatorAdapter(SQLSafetyPolicy()),
        executor=DatasetSQLQueryExecutor(data_source, execution_policy),
        charts=AIChartSelectorAdapter(),
        answers=AIAnswerWriterAdapter(),
        suggestions=QuerySuggestionAdapter(),
    )


def execute_legacy_ai_query(
    question: str,
    dataset_id: int,
    schema: dict,
    history: list[dict] | None = None,
    *,
    data_source,
) -> dict:
    """Compatibilidad temporal: adapta el contrato dict al caso de uso actual."""
    request = AIQueryRequestDTO(
        question=question,
        dataset_id=dataset_id,
        schema=schema,
        history=tuple(
            ConversationTurnDTO(question=turn["question"], sql=turn["sql"])
            for turn in (history or ())
        ),
    )
    result = build_ai_query_engine(data_source).execute(request)
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


def build_statistical_analysis_engine(data_source=None) -> ExecuteStatisticalAnalysis:
    """Compone el caso de uso estadístico con sus adaptadores concretos."""
    source = data_source
    if source is None:
        source = DatasetQueryDataSource(DjangoDatasetRepository())
    return ExecuteStatisticalAnalysis(
        calculator=PandasStatisticalAnalysisCalculator(source),
        answers=StatisticalAnalysisAnswerWriterAdapter(),
        suggestions=QuerySuggestionAdapter(),
    )


def execute_legacy_statistical_analysis(
    analysis_type: str,
    dataset_id: int,
    question: str,
    *,
    data_source=None,
) -> dict:
    """Adapta la interfaz dict legacy al caso de uso estadístico actual."""
    datasets = DjangoDatasetRepository()
    dataset = datasets.get_by_id(dataset_id)
    if dataset is None:
        raise ValueError(f"No existe el dataset {dataset_id}")

    result = build_statistical_analysis_engine(data_source).execute(
        AnalysisQueryRequestDTO(
            intent=analysis_type,
            dataset_id=dataset_id,
            question=question,
            schema=dataset.schema_json,
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


def build_query_use_cases() -> dict[str, object]:
    datasets = DjangoDatasetRepository()
    data_source = DatasetQueryDataSource(datasets)
    histories = DjangoQueryHistoryRepository()
    results = DjangoQueryResultRepository()
    feedback = DjangoQueryFeedbackRepository()
    execute = ExecuteQuery(
        datasets=datasets,
        histories=histories,
        results=results,
        profiles=DjangoProfileRepository(),
        cache=DjangoQueryCache(),
        materializer=QueryDatasetMaterializer(),
        ai_engine=build_ai_query_engine(data_source),
        analysis_engine=ExecuteStatisticalAnalysis(
            calculator=PandasStatisticalAnalysisCalculator(data_source),
            answers=StatisticalAnalysisAnswerWriterAdapter(),
            suggestions=QuerySuggestionAdapter(),
        ),
        transaction=DjangoQueryTransaction(),
        waiter=ThreadWaiter(),
        default_model_name=getattr(settings, "LLM_SQL_MODEL", ""),
    )
    return {
        "execute": execute,
        "list_history": ListQueryHistory(histories),
        "get_detail": GetQueryDetail(histories, results),
        "submit_feedback": SubmitQueryFeedback(histories, feedback),
        "histories": histories,
        "results": results,
        "feedback": feedback,
    }
