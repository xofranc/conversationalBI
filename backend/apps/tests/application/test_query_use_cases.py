from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from apps.dataset.domain.entities import Dataset, DatasetStatus
from apps.queries.application.dtos import (
    EngineResultDTO,
    ExecuteQueryInput,
    GetQueryDetailInput,
    ListQueryHistoryInput,
    QueryCacheKeyDTO,
    QueryResponseDTO,
    SubmitFeedbackInput,
)
from apps.queries.application.use_cases import (
    DatasetNotFound,
    DatasetNotReady,
    ExecuteQuery,
    FeedbackAlreadyExists,
    GetQueryDetail,
    InvalidFeedbackScoreInput,
    ListQueryHistory,
    QueryAccessDenied,
    QueryNotFound,
    SubmitQueryFeedback,
)
from apps.queries.domain.entities import QueryFeedback, QueryHistory, QueryResult
from apps.queries.domain.exceptions import InvalidFeedbackScore
from apps.queries.domain.value_objects import ChartType, FeedbackScore
from apps.users.domain.entities import Profile


class DatasetMemory:
    def __init__(self, dataset):
        self.dataset = dataset

    def get_by_id(self, dataset_id):
        return self.dataset if self.dataset and self.dataset.id == dataset_id else None

    def save(self, dataset):
        self.dataset = dataset
        return dataset


class HistoryMemory:
    def __init__(self, queries=()):
        self.items = {item.id: item for item in queries if item.id is not None}
        self.next_id = max(self.items, default=0) + 1

    def get_by_id(self, query_id):
        return self.items.get(query_id)

    def list_by_user(self, user_id):
        return tuple(item for item in self.items.values() if item.user_id == user_id)

    def list_by_dataset(self, dataset_id):
        return tuple(item for item in self.items.values() if item.dataset_id == dataset_id)

    def save(self, query):
        if query.id is None:
            query = replace(query, id=self.next_id)
            self.next_id += 1
        self.items[query.id] = query
        return query


class ResultMemory:
    def __init__(self):
        self.items = {}

    def get_by_query_id(self, query_id):
        return self.items.get(query_id)

    def save(self, result):
        self.items[result.query_id] = result
        return result


class ProfileMemory:
    def __init__(self):
        self.items = {}

    def increment_query_count(self, user_id):
        profile = self.items.get(user_id, Profile(user_id=user_id))
        self.items[user_id] = profile.increment_query_count()


class Cache:
    def __init__(self):
        self.values = {}
        self.lock = True
        self.released = []

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value):
        self.values[key] = value

    def acquire_lock(self, key):
        return self.lock

    def release_lock(self, key):
        self.released.append(key)


class Materializer:
    def __init__(self, path=None):
        self.path = path
        self.calls = []

    def ensure_available(self, dataset_id, file_path, materialized_path):
        self.calls.append((dataset_id, file_path, materialized_path))
        return self.path if self.path is not None else materialized_path


class Engine:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def execute(self, request):
        self.calls.append(request)
        return self.result


class NoWait:
    def sleep(self, seconds):
        raise AssertionError("unexpected wait")


class Atomic:
    @contextmanager
    def atomic(self):
        yield


_DEFAULT_DATASET = object()


def make_query_use_case(dataset=_DEFAULT_DATASET, *, engine_result=None, cached=None, materializer=None):
    if dataset is _DEFAULT_DATASET:
        dataset = Dataset(
        id=5, user_id=2, name="sales", file_path="sales.csv", db_path="db/5",
        status=DatasetStatus.READY, schema_json={"tables": []},
        )
    datasets = DatasetMemory(dataset)
    histories, results, profiles, cache = HistoryMemory(), ResultMemory(), ProfileMemory(), Cache()
    ai = Engine(engine_result or EngineResultDTO(
        sql="SELECT 1", success=True, rows=({"count": 1},), columns=({"name": "count"},),
        chart_type="table", answer="one", model_used="test-model",
    ))
    analysis = Engine(EngineResultDTO(sql="SELECT 1", success=True, rows=({"count": 1},)))
    if cached is not None:
        cache.values[QueryCacheKeyDTO("how many?", 5, "")] = cached
    use_case = ExecuteQuery(
        datasets, histories, results, profiles, cache,
        materializer or Materializer(), ai, analysis, Atomic(), NoWait(),
        default_model_name="fallback-model",
    )
    return use_case, datasets, histories, results, profiles, cache, ai, analysis


def test_execute_query_persists_history_result_and_increments_quota():
    use_case, _datasets, histories, results, profiles, cache, ai, _analysis = make_query_use_case()
    response = use_case.execute(ExecuteQueryInput(2, 5, "How many?"))
    assert response.success and response.query_id == 1 and response.cached is False
    assert response.data == ({"count": 1},) and response.row_count == 1
    assert histories.get_by_id(1).model_used == "test-model"
    assert results.get_by_query_id(1).chart_type is ChartType.TABLE
    assert profiles.items[2].query_count == 1
    assert len(cache.values) == 1 and len(ai.calls) == 1 and cache.released


def test_cache_hit_creates_fresh_history_and_counts_the_new_query_only():
    cached_response = QueryResponseDTO(
        query_id=90, sql="SELECT count(*)", success=True, error_message="", execution_time=1.2,
        model_used="cached-model", retry_count=1, cached=False, data=({"n": 8},), columns=(),
        chart_type="bar", chart_config={}, row_count=1, answer="eight",
    )
    use_case, _datasets, histories, results, profiles, _cache, ai, _analysis = make_query_use_case(cached=cached_response)
    result = use_case.execute(ExecuteQueryInput(2, 5, " HOW MANY? "))
    assert result.cached and result.query_id == 1 and result.query_id != cached_response.query_id
    assert result.sql == cached_response.sql and result.data == cached_response.data
    assert histories.get_by_id(result.query_id).cached
    assert not results.items and profiles.items[2].query_count == 1 and not ai.calls


@pytest.mark.parametrize("reason", ["missing", "owner", "not_ready"])
def test_execute_query_validates_existence_ownership_and_ready_before_engines(reason):
    dataset = None if reason == "missing" else Dataset(
        id=5, user_id=3 if reason == "owner" else 2, name="sales", file_path="sales.csv",
        status=DatasetStatus.ERROR if reason == "not_ready" else DatasetStatus.READY,
    )
    use_case, _datasets, _histories, _results, _profiles, _cache, ai, analysis = make_query_use_case(dataset)
    expected = DatasetNotFound if reason == "missing" else QueryAccessDenied if reason == "owner" else DatasetNotReady
    with pytest.raises(expected):
        use_case.execute(ExecuteQueryInput(2, 5, "How many?"))
    assert not ai.calls and not analysis.calls


def test_materializer_path_update_and_failure_response_are_persisted_consistently():
    materializer = Materializer("db/recovered")
    failed = EngineResultDTO(success=False, error_message="invalid request", suggestions=("try again",))
    use_case, datasets, histories, results, profiles, cache, _ai, _analysis = make_query_use_case(
        engine_result=failed, materializer=materializer,
    )
    response = use_case.execute(ExecuteQueryInput(2, 5, "show all rows"))
    assert response.success is False and response.suggestions == ("try again",)
    assert histories.get_by_id(response.query_id).error_msg == "invalid request"
    assert not results.items and not cache.values
    assert datasets.dataset.db_path == "db/recovered"
    assert profiles.items[2].query_count == 1


def test_analysis_intent_is_sent_to_analysis_engine_instead_of_ai_engine():
    use_case, _datasets, _histories, _results, _profiles, _cache, ai, analysis = make_query_use_case()
    result = use_case.execute(ExecuteQueryInput(2, 5, "pronóstico de ventas"))
    assert result.success and not ai.calls
    assert analysis.calls[0].intent == "forecast"


def test_ai_context_uses_only_recent_successful_uncached_sql_from_same_owner():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    previous = [
        QueryHistory(id=1, user_id=2, dataset_id=5, question="Q1", sql_generated="SELECT 1", success=True, created_at=start),
        QueryHistory(id=2, user_id=2, dataset_id=5, question="Q2", sql_generated="SELECT 2", success=True, created_at=start + timedelta(days=1)),
        QueryHistory(id=3, user_id=2, dataset_id=5, question="Q3", sql_generated="SELECT 3", success=True, created_at=start + timedelta(days=2)),
        QueryHistory(id=4, user_id=2, dataset_id=5, question="cached", sql_generated="SELECT 4", success=True, cached=True, created_at=start + timedelta(days=3)),
        QueryHistory(id=5, user_id=9, dataset_id=5, question="other", sql_generated="SELECT 5", success=True, created_at=start + timedelta(days=4)),
        QueryHistory(id=6, user_id=2, dataset_id=5, question="failed", sql_generated="SELECT 6", success=False, created_at=start + timedelta(days=5)),
        QueryHistory(id=7, user_id=2, dataset_id=5, question="comment", sql_generated="-- disabled", success=True, created_at=start + timedelta(days=6)),
    ]
    use_case, _datasets, histories, _results, _profiles, _cache, ai, _analysis = make_query_use_case()
    histories.items.update({query.id: query for query in previous})
    use_case.execute(ExecuteQueryInput(2, 5, "List the records"))
    context = ai.calls[0].history
    assert [(turn.question, turn.sql) for turn in context] == [
        ("Q1", "SELECT 1"), ("Q2", "SELECT 2"), ("Q3", "SELECT 3"),
    ]


def test_lock_contention_rechecks_cache_then_persists_cache_hit_without_releasing_other_lock():
    cached = QueryResponseDTO(
        query_id=8, sql="SELECT 8", success=True, error_message="", execution_time=1,
        model_used="cached", retry_count=0, cached=False, data=({"n": 8},), columns=(),
        chart_type="table", chart_config={}, row_count=1, answer="eight",
    )
    use_case, _datasets, histories, _results, profiles, cache, ai, _analysis = make_query_use_case()

    class ContendedCache(Cache):
        def acquire_lock(self, key):
            self.key = key
            return False

    cache = ContendedCache()
    use_case._cache = cache

    class CacheOnWait:
        def sleep(self, seconds):
            cache.values[cache.key] = cached

    use_case._waiter = CacheOnWait()
    response = use_case.execute(ExecuteQueryInput(2, 5, "How many?"))
    assert response.cached and response.sql == "SELECT 8" and response.query_id == 1
    assert histories.get_by_id(1).cached and profiles.items[2].query_count == 1
    assert not cache.released and not ai.calls


def test_lock_contention_without_populated_cache_falls_back_to_engine():
    use_case, _datasets, histories, _results, profiles, cache, ai, _analysis = make_query_use_case()
    cache.lock = False

    class NoOpWait:
        def sleep(self, _seconds):
            return None

    use_case._waiter = NoOpWait()
    response = use_case.execute(ExecuteQueryInput(2, 5, "How many?"))
    assert response.success and histories.get_by_id(response.query_id) is not None
    assert profiles.items[2].query_count == 1 and len(ai.calls) == 1
    assert not cache.released


def test_history_list_filters_by_dataset_sorts_newest_and_detail_is_owner_scoped():
    older = datetime(2026, 1, 1, tzinfo=timezone.utc)
    newer = older + timedelta(days=1)
    histories = HistoryMemory([
        QueryHistory(id=1, user_id=2, dataset_id=5, question="older", created_at=older),
        QueryHistory(id=2, user_id=2, dataset_id=6, question="other", created_at=newer),
        QueryHistory(id=3, user_id=2, dataset_id=5, question="newer", created_at=newer),
        QueryHistory(id=4, user_id=9, dataset_id=5, question="private", created_at=newer),
    ])
    listed = ListQueryHistory(histories).execute(ListQueryHistoryInput(2, dataset_id=5))
    assert [entry.question for entry in listed] == ["newer", "older"]
    assert len(ListQueryHistory(histories).execute(ListQueryHistoryInput(2))) == 3
    result_repo = ResultMemory()
    result_repo.save(QueryResult(query_id=3, result_json=[{"x": 1}], chart_type=ChartType.BAR))
    detail = GetQueryDetail(histories, result_repo).execute(GetQueryDetailInput(2, 3))
    assert detail.result.data == ({"x": 1},) and detail.result.chart_type == "bar"
    with pytest.raises(QueryNotFound):
        GetQueryDetail(histories, result_repo).execute(GetQueryDetailInput(2, 4))
    with pytest.raises(QueryNotFound):
        GetQueryDetail(histories, result_repo).execute(GetQueryDetailInput(2, 404))
    no_result = GetQueryDetail(histories, result_repo).execute(GetQueryDetailInput(2, 1))
    assert no_result.result is None


def test_feedback_validates_query_owner_score_duplicate_and_saved_response():
    histories = HistoryMemory([
        QueryHistory(id=3, user_id=2, dataset_id=5, question="total?"),
        QueryHistory(id=4, user_id=2, dataset_id=5, question="another?"),
    ])

    class FeedbackMemory:
        def __init__(self):
            self.item = None

        def get_by_query_id(self, query_id):
            return self.item if self.item and self.item.query_id == query_id else None

        def save(self, feedback):
            self.item = replace(feedback, id=1)
            return self.item

    feedback = FeedbackMemory()
    use_case = SubmitQueryFeedback(histories, feedback)
    dto = use_case.execute(SubmitFeedbackInput(2, 3, 1, "useful"))
    assert (dto.query_id, dto.score, dto.comment) == (3, 1, "useful")
    with pytest.raises(FeedbackAlreadyExists):
        use_case.execute(SubmitFeedbackInput(2, 3, -1))
    with pytest.raises(QueryNotFound):
        use_case.execute(SubmitFeedbackInput(2, 404, 1))
    with pytest.raises(QueryNotFound):
        use_case.execute(SubmitFeedbackInput(9, 3, 1))
    with pytest.raises(InvalidFeedbackScoreInput, match="feedback debe ser útil"):
        use_case.execute(SubmitFeedbackInput(2, 4, 0))


@pytest.mark.parametrize("score", [0, 2, -2])
def test_feedback_score_error_message_is_translated_from_domain(score):
    histories = HistoryMemory([QueryHistory(id=3, user_id=2, dataset_id=5, question="total?")])

    class FeedbackMemory:
        def get_by_query_id(self, _query_id):
            return None

        def save(self, _feedback):
            raise AssertionError("invalid feedback must not be persisted")

    use_case = SubmitQueryFeedback(histories, FeedbackMemory())
    with pytest.raises(InvalidFeedbackScore) as domain_error:
        FeedbackScore.from_value(score)

    with pytest.raises(InvalidFeedbackScoreInput) as application_error:
        use_case.execute(SubmitFeedbackInput(2, 3, score))

    assert str(application_error.value) == str(domain_error.value)
