"""Composition root: build infrastructure adapters and inject application ports."""

from django.conf import settings

from apps.core.application.use_cases import (
    CleanupDemoSession,
    CleanupExpiredDemoSessions,
    GetOrCreateDemoSession,
    GetOrCreateDemoUser,
    ListDemoSessionDatasets,
)
from apps.core.infrastructure.adapters import DjangoClock, DjangoDemoDatasetLifecycle
from apps.core.infrastructure.repositories import DjangoDemoSessionRepository
from apps.core.interfaces.identity import request_identity
from apps.core.interfaces.permissions import IsAuthenticatedOrDemo
from apps.core.interfaces.urls import create_urlpatterns as create_core_urlpatterns
from apps.dataset.application.use_cases import (
    CreateDataset,
    DeleteDataset,
    GetDataset,
    ListDatasets,
    ProcessDataset,
)
from apps.dataset.infrastructure.adapters import (
    DjangoDatasetFileStorage,
    DjangoDatasetResourceCleanup,
    DjangoDatasetSchemaExtractor,
    PostgresDatasetMaterializer,
)
from apps.dataset.infrastructure.query_data_source import DatasetQueryDataSource
from apps.dataset.infrastructure.repositories import (
    DjangoDatasetRepository,
    DjangoDatasetTableRepository,
)
from apps.dataset.interfaces.urls import create_urlpatterns as create_dataset_urlpatterns
from apps.project_status.application.use_cases import (
    GetProjectStatus,
    ListProjectModules,
    ListProjectPhases,
)
from apps.project_status.infrastructure.repositories import (
    DjangoProjectModuleRepository,
    DjangoProjectPhaseRepository,
)
from apps.project_status.interfaces.urls import (
    create_urlpatterns as create_project_status_urlpatterns,
)
from apps.queries.application.execute_statistical_analysis import (
    ExecuteStatisticalAnalysis,
)
from apps.queries.application.generate_ai_query import GenerateAIQuery
from apps.queries.application.use_cases import (
    ExecuteQuery,
    GetQueryDetail,
    ListQueryHistory,
    SubmitQueryFeedback,
)
from apps.queries.domain.policies import QueryExecutionPolicy, SQLSafetyPolicy
from apps.queries.infrastructure.adapters import (
    DjangoQueryCache,
    DjangoQueryTransaction,
    ThreadWaiter,
)
from apps.queries.infrastructure.ai.adapters import (
    AIAnswerWriterAdapter,
    AIChartSelectorAdapter,
    AIPromptComposerAdapter,
    DatasetSQLQueryExecutor,
    QuerySuggestionAdapter,
    SQLQueryGeneratorAdapter,
    SQLSafetyValidatorAdapter,
)
from apps.queries.infrastructure.analysis.adapters import (
    PandasStatisticalAnalysisCalculator,
)
from apps.queries.infrastructure.repositories import (
    DjangoQueryFeedbackRepository,
    DjangoQueryHistoryRepository,
    DjangoQueryResultRepository,
)
from apps.queries.interfaces.urls import create_urlpatterns as create_query_urlpatterns
from apps.users.application.use_cases import (
    AuthenticateExternalIdentity,
    CanAccessDataset,
    GetProfile,
    GetQuota,
    IncrementQueryUsage,
    UpdateProfile,
)
from apps.users.infrastructure.adapters import SupabaseAuthenticator
from apps.users.infrastructure.repositories import (
    DjangoProfileRepository,
    DjangoUserRepository,
)
from apps.users.interfaces.urls import create_urlpatterns as create_user_urlpatterns


def build_ai_query_engine(data_source) -> GenerateAIQuery:
    """Compose AI orchestration and its concrete infrastructure adapters."""
    return GenerateAIQuery(
        prompts=AIPromptComposerAdapter(),
        generator=SQLQueryGeneratorAdapter(),
        safety=SQLSafetyValidatorAdapter(SQLSafetyPolicy()),
        executor=DatasetSQLQueryExecutor(data_source, QueryExecutionPolicy()),
        charts=AIChartSelectorAdapter(),
        answers=AIAnswerWriterAdapter(),
        suggestions=QuerySuggestionAdapter(),
    )


def build_statistical_analysis_engine(data_source=None) -> ExecuteStatisticalAnalysis:
    """Compose statistical analysis with its concrete infrastructure adapters."""
    source = data_source
    if source is None:
        source = DatasetQueryDataSource(DjangoDatasetRepository())
    return ExecuteStatisticalAnalysis(
        calculator=PandasStatisticalAnalysisCalculator(source),
        answers=AIAnswerWriterAdapter(),
        suggestions=QuerySuggestionAdapter(),
    )


def build_core_use_cases() -> dict[str, object]:
    sessions = DjangoDemoSessionRepository()
    clock = DjangoClock()
    get_user = GetOrCreateDemoUser(DjangoUserRepository())
    datasets = DjangoDatasetRepository()
    resource_cleanup = DjangoDatasetResourceCleanup(
        datasets, DjangoDatasetFileStorage(), PostgresDatasetMaterializer()
    )
    lifecycle = DjangoDemoDatasetLifecycle(datasets, resource_cleanup)
    cleanup_session = CleanupDemoSession(get_user, lifecycle)
    return {
        "get_or_create_session": GetOrCreateDemoSession(sessions, clock),
        "get_or_create_user": get_user,
        "list_datasets": ListDemoSessionDatasets(get_user, lifecycle),
        "cleanup_session": cleanup_session,
        "cleanup_expired_sessions": CleanupExpiredDemoSessions(
            sessions, cleanup_session, clock
        ),
        "sessions": sessions,
    }


def build_dataset_use_cases() -> dict[str, object]:
    datasets = DjangoDatasetRepository()
    tables = DjangoDatasetTableRepository()
    files = DjangoDatasetFileStorage()
    materializer = PostgresDatasetMaterializer()
    resource_cleanup = DjangoDatasetResourceCleanup(datasets, files, materializer)
    process = ProcessDataset(
        datasets, tables, materializer, DjangoDatasetSchemaExtractor()
    )
    return {
        "create": CreateDataset(datasets, files, process),
        "process": process,
        "list": ListDatasets(datasets),
        "get": GetDataset(datasets, tables),
        "delete": DeleteDataset(datasets, resource_cleanup),
        "datasets": datasets,
        "tables": tables,
    }


def build_project_status_use_cases() -> dict[str, object]:
    phases = ListProjectPhases(DjangoProjectPhaseRepository())
    modules = ListProjectModules(DjangoProjectModuleRepository())
    return {
        "list_phases": phases,
        "list_modules": modules,
        "get_status": GetProjectStatus(phases, modules),
    }


def build_query_use_cases() -> dict[str, object]:
    datasets = DjangoDatasetRepository()
    data_source = DatasetQueryDataSource(datasets)
    histories = DjangoQueryHistoryRepository()
    results = DjangoQueryResultRepository()
    feedback = DjangoQueryFeedbackRepository()
    query_materializer = PostgresDatasetMaterializer()
    execute = ExecuteQuery(
        datasets=datasets,
        histories=histories,
        results=results,
        profiles=DjangoProfileRepository(),
        cache=DjangoQueryCache(),
        materializer=query_materializer,
        ai_engine=build_ai_query_engine(data_source),
        analysis_engine=build_statistical_analysis_engine(data_source),
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


def build_user_use_cases() -> dict[str, object]:
    profiles = DjangoProfileRepository()
    datasets = DjangoDatasetRepository()
    return {
        "authenticate": AuthenticateExternalIdentity(SupabaseAuthenticator()),
        "get_profile": GetProfile(profiles),
        "update_profile": UpdateProfile(profiles),
        "get_quota": GetQuota(profiles),
        "increment_query_usage": IncrementQueryUsage(profiles),
        "can_access_dataset": CanAccessDataset(datasets),
        "users": DjangoUserRepository(),
    }


def build_interface_urlpatterns():
    """Build each use-case bundle once and inject it into its module routes."""
    core_use_cases = build_core_use_cases()

    identity_provider = lambda request: request_identity(request, core_use_cases)

    return {
        "project_status": create_project_status_urlpatterns(
            build_project_status_use_cases()
        ),
        "users": create_user_urlpatterns(build_user_use_cases()),
        "dataset": create_dataset_urlpatterns(
            build_dataset_use_cases(),
            identity_provider=identity_provider,
            permission_class=IsAuthenticatedOrDemo,
        ),
        "queries": create_query_urlpatterns(
            build_query_use_cases(),
            identity_provider=identity_provider,
            permission_class=IsAuthenticatedOrDemo,
        ),
        "core": create_core_urlpatterns(core_use_cases),
    }


def build_core_urlpatterns():
    return create_core_urlpatterns(build_core_use_cases())


def build_cleanup_expired_sessions_use_case():
    """Compose core cleanup for non-HTTP entry points."""
    return build_core_use_cases()["cleanup_expired_sessions"]


def build_dataset_urlpatterns():
    core_use_cases = build_core_use_cases()

    identity_provider = lambda request: request_identity(request, core_use_cases)

    return create_dataset_urlpatterns(
        build_dataset_use_cases(),
        identity_provider=identity_provider,
        permission_class=IsAuthenticatedOrDemo,
    )


def build_project_status_urlpatterns():
    return create_project_status_urlpatterns(build_project_status_use_cases())


def build_query_urlpatterns():
    core_use_cases = build_core_use_cases()

    identity_provider = lambda request: request_identity(request, core_use_cases)

    return create_query_urlpatterns(
        build_query_use_cases(),
        identity_provider=identity_provider,
        permission_class=IsAuthenticatedOrDemo,
    )


def build_user_urlpatterns():
    return create_user_urlpatterns(build_user_use_cases())
