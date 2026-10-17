"""Casos de uso para ejecutar preguntas y consultar historial/feedback."""

from __future__ import annotations

from dataclasses import replace
from apps.dataset.domain.exceptions import DatasetNotQueryable
from apps.queries.domain.exceptions import InvalidFeedbackScore
from apps.dataset.domain.policies import DatasetOwnershipPolicy
from apps.dataset.domain.repositories import DatasetRepository
from apps.queries.domain.entities import QueryFeedback, QueryHistory, QueryResult
from apps.queries.domain.policies import AnalysisIntentPolicy
from apps.queries.domain.repositories import (
    QueryFeedbackRepository,
    QueryHistoryRepository,
    QueryResultRepository,
)
from apps.queries.domain.value_objects import ChartType, FeedbackScore
from apps.users.domain.repositories import ProfileRepository

from .dtos import (
    AIQueryRequestDTO,
    AnalysisQueryRequestDTO,
    ConversationTurnDTO,
    EngineResultDTO,
    ExecuteQueryInput,
    FeedbackDTO,
    GetQueryDetailInput,
    ListQueryHistoryInput,
    QueryCacheKeyDTO,
    QueryDetailDTO,
    QueryHistoryItemDTO,
    QueryResponseDTO,
    QueryResultDTO,
    SubmitFeedbackInput,
)
from .ports import (
    AIQueryEngine,
    QueryCache,
    QueryDatasetMaterializer,
    QueryTransaction,
    StatisticalAnalysisEngine,
    Waiter,
)


class QueryNotFound(LookupError):
    """La consulta no existe o no pertenece al usuario actual."""


class QueryAccessDenied(PermissionError):
    """El usuario no es propietario del dataset consultado."""


class FeedbackAlreadyExists(ValueError):
    """Ya hay feedback para esta consulta (incluye conflicto de unicidad)."""


class InvalidFeedbackScoreInput(ValueError):
    """El score de feedback recibido no es válido."""


class DatasetNotFound(LookupError):
    """No existe el dataset solicitado."""


class DatasetNotReady(RuntimeError):
    """El dataset no está listo para ejecutar consultas."""


def _response_from_cache(cached: QueryResponseDTO, query_id: int | None) -> QueryResponseDTO:
    return replace(cached, query_id=query_id, cached=True)


def _query_response(
    history: QueryHistory,
    result: QueryResult | None,
    engine_result: EngineResultDTO,
    *,
    cached: bool,
) -> QueryResponseDTO:
    return QueryResponseDTO(
        query_id=history.id,
        sql=history.sql_generated,
        success=history.success,
        error_message=history.error_msg,
        execution_time=history.execution_time,
        model_used=history.model_used,
        retry_count=history.retry_count,
        cached=cached,
        data=tuple(result.result_json) if result else (),
        columns=tuple(result.columns) if result else (),
        chart_type=result.chart_type.value if result else ChartType.TABLE.value,
        chart_config=result.chart_config if result else {},
        row_count=result.row_count if result else 0,
        answer=result.answer if result else "",
        suggestions=engine_result.suggestions if not history.success else (),
    )


class ExecuteQuery:
    """Guarda ownership/READY, resuelve caché, delega motores y persiste."""

    CACHE_WAIT_ATTEMPTS = 5
    CACHE_WAIT_SECONDS = 1.0
    HISTORY_CONTEXT_SIZE = 3

    def __init__(
        self,
        datasets: DatasetRepository,
        histories: QueryHistoryRepository,
        results: QueryResultRepository,
        profiles: ProfileRepository,
        cache: QueryCache,
        materializer: QueryDatasetMaterializer,
        ai_engine: AIQueryEngine,
        analysis_engine: StatisticalAnalysisEngine,
        transaction: QueryTransaction,
        waiter: Waiter,
        *,
        default_model_name: str = "",
    ) -> None:
        self._datasets = datasets
        self._histories = histories
        self._results = results
        self._profiles = profiles
        self._cache = cache
        self._materializer = materializer
        self._ai_engine = ai_engine
        self._analysis_engine = analysis_engine
        self._transaction = transaction
        self._waiter = waiter
        self._default_model_name = default_model_name

    def execute(self, request: ExecuteQueryInput) -> QueryResponseDTO:
        dataset = self._datasets.get_by_id(request.dataset_id)
        if dataset is None:
            raise DatasetNotFound(f"Dataset {request.dataset_id} no encontrado")
        if not DatasetOwnershipPolicy.owns(dataset, request.user_id):
            raise QueryAccessDenied("No tienes acceso a este dataset")
        try:
            dataset.ensure_queryable()
        except DatasetNotQueryable as exc:
            raise DatasetNotReady(str(exc)) from exc

        materialized_path = self._materializer.ensure_available(
            request.dataset_id,
            dataset.file_path,
            dataset.db_path,
        )
        if materialized_path != dataset.db_path:
            dataset = self._datasets.save(replace(dataset, db_path=materialized_path))

        version = dataset.updated_at.isoformat() if dataset.updated_at else ""
        cache_key = QueryCacheKeyDTO(request.question.strip().lower(), request.dataset_id, version)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return self._persist_cache_hit(request, cached)

        got_lock = self._cache.acquire_lock(cache_key)
        try:
            if not got_lock:
                for _ in range(self.CACHE_WAIT_ATTEMPTS):
                    self._waiter.sleep(self.CACHE_WAIT_SECONDS)
                    cached = self._cache.get(cache_key)
                    if cached is not None:
                        return self._persist_cache_hit(request, cached)

            intent = AnalysisIntentPolicy.detect(request.question)
            if intent is None:
                engine_result = self._ai_engine.execute(AIQueryRequestDTO(
                    question=request.question,
                    dataset_id=request.dataset_id,
                    schema=dataset.schema_json,
                    history=self._conversation_context(request.user_id, request.dataset_id),
                ))
            else:
                engine_result = self._analysis_engine.execute(AnalysisQueryRequestDTO(
                    intent=intent.value,
                    dataset_id=request.dataset_id,
                    question=request.question,
                    schema=dataset.schema_json,
                ))

            history = QueryHistory(
                user_id=request.user_id,
                dataset_id=request.dataset_id,
                question=request.question,
                sql_generated=engine_result.sql,
                execution_time=engine_result.execution_time,
                success=engine_result.success,
                error_msg=engine_result.error_message,
                model_used=engine_result.model_used or self._default_model_name,
                retry_count=engine_result.retry_count,
                cached=False,
            )
            result_entity: QueryResult | None = None
            with self._transaction.atomic():
                history = self._histories.save(history)
                if engine_result.success:
                    if history.id is None:
                        raise RuntimeError("El repositorio debe asignar identidad a la consulta")
                    chart_type = ChartType(engine_result.chart_type)
                    result_entity = self._results.save(QueryResult(
                        query_id=history.id,
                        result_json=list(engine_result.rows),
                        columns=list(engine_result.columns),
                        row_count=len(engine_result.rows),
                        answer=engine_result.answer,
                        chart_type=chart_type,
                        chart_config=engine_result.chart_config or {},
                    ))

            # La cuota solo se registra; su disponibilidad nunca bloquea el caso de uso.
            self._profiles.increment_query_count(request.user_id)
            response = _query_response(history, result_entity, engine_result, cached=False)
            if engine_result.success:
                self._cache.set(cache_key, response)
            return response
        finally:
            if got_lock:
                self._cache.release_lock(cache_key)

    def _persist_cache_hit(
        self, request: ExecuteQueryInput, cached: QueryResponseDTO
    ) -> QueryResponseDTO:
        # La consulta nueva queda anclada al dataset actual, no al ID cacheado.
        history = QueryHistory(
            user_id=request.user_id,
            dataset_id=request.dataset_id,
            question=request.question,
            sql_generated=cached.sql,
            execution_time=0.0,
            success=True,
            model_used=cached.model_used,
            retry_count=0,
            cached=True,
        )
        with self._transaction.atomic():
            saved = self._histories.save(history)
        self._profiles.increment_query_count(request.user_id)
        return _response_from_cache(cached, saved.id)

    def _conversation_context(self, user_id: int, dataset_id: int) -> tuple[ConversationTurnDTO, ...]:
        candidates = [
            query
            for query in self._histories.list_by_dataset(dataset_id)
            if query.user_id == user_id
            and query.success
            and not query.cached
            and query.sql_generated
            and not query.sql_generated.startswith("--")
        ]
        candidates.sort(
            key=lambda query: query.created_at.isoformat() if query.created_at else "",
            reverse=True,
        )
        return tuple(
            ConversationTurnDTO(question=query.question, sql=query.sql_generated)
            for query in reversed(candidates[: self.HISTORY_CONTEXT_SIZE])
        )


class ListQueryHistory:
    """Lista historial propio con opción de filtrar por dataset."""

    def __init__(self, histories: QueryHistoryRepository) -> None:
        self._histories = histories

    def execute(self, request: ListQueryHistoryInput) -> tuple[QueryHistoryItemDTO, ...]:
        queries = self._histories.list_by_user(request.user_id)
        if request.dataset_id is not None:
            queries = [query for query in queries if query.dataset_id == request.dataset_id]
        queries = sorted(
            queries,
            key=lambda query: query.created_at.isoformat() if query.created_at else "",
            reverse=True,
        )
        return tuple(
            QueryHistoryItemDTO(
                query_id=query.id,
                question=query.question,
                success=query.success,
                execution_time=query.execution_time,
                model_used=query.model_used,
                retry_count=query.retry_count,
                cached=query.cached,
                created_at=query.created_at,
            )
            for query in queries
        )


class GetQueryDetail:
    """Obtiene detalle y resultado solo para el dueño de la consulta."""

    def __init__(self, histories: QueryHistoryRepository, results: QueryResultRepository) -> None:
        self._histories = histories
        self._results = results

    def execute(self, request: GetQueryDetailInput) -> QueryDetailDTO:
        query = self._histories.get_by_id(request.query_id)
        if query is None or query.user_id != request.user_id:
            raise QueryNotFound(f"Consulta {request.query_id} no encontrada")
        result = self._results.get_by_query_id(request.query_id)
        result_dto = None
        if result is not None:
            result_dto = QueryResultDTO(
                data=tuple(result.result_json),
                columns=tuple(result.columns),
                row_count=result.row_count,
                chart_type=result.chart_type.value,
                chart_config=result.chart_config,
                answer=result.answer,
            )
        return QueryDetailDTO(
            query_id=query.id,
            question=query.question,
            sql=query.sql_generated,
            execution_time=query.execution_time,
            success=query.success,
            error_message=query.error_msg,
            model_used=query.model_used,
            retry_count=query.retry_count,
            cached=query.cached,
            created_at=query.created_at,
            result=result_dto,
        )


class SubmitQueryFeedback:
    """Crea feedback +/-1 respetando ownership y cardinalidad uno-a-uno."""

    def __init__(
        self,
        histories: QueryHistoryRepository,
        feedback: QueryFeedbackRepository,
    ) -> None:
        self._histories = histories
        self._feedback = feedback

    def execute(self, request: SubmitFeedbackInput) -> FeedbackDTO:
        query = self._histories.get_by_id(request.query_id)
        if query is None or query.user_id != request.user_id:
            raise QueryNotFound(f"Consulta {request.query_id} no encontrada")
        if self._feedback.get_by_query_id(request.query_id) is not None:
            raise FeedbackAlreadyExists("Ya existe feedback para esta consulta")

        try:
            score = FeedbackScore.from_value(request.score)
        except InvalidFeedbackScore as error:
            raise InvalidFeedbackScoreInput(str(error)) from error

        saved = self._feedback.save(QueryFeedback(
            query_id=request.query_id,
            score=score,
            comment=request.comment,
        ))
        return FeedbackDTO(
            query_id=saved.query_id,
            score=int(saved.score),
            comment=saved.comment,
            created_at=saved.created_at,
        )
