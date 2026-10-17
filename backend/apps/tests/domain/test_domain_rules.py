from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import pytest

from apps.core.domain.entities import DEMO_SESSION_TTL, DemoSession
from apps.core.domain.exceptions import InvalidSessionIdentifier
from apps.core.domain.value_objects import SessionIdentifier
from apps.dataset.domain.entities import Dataset, DatasetStatus
from apps.dataset.domain.exceptions import DatasetFileTooLarge, DatasetNotQueryable
from apps.dataset.domain.policies import DatasetOwnershipPolicy, DatasetUploadPolicy
from apps.project_status.domain.entities import (
    ProjectModule,
    ProjectModuleStatus,
    ProjectPhase,
    ProjectPhaseStatus,
)
from apps.queries.domain.entities import QueryFeedback, QueryHistory, QueryResult
from apps.queries.domain.exceptions import InvalidFeedbackScore
from apps.queries.domain.exceptions import InvalidPolicyConfiguration
from apps.queries.domain.policies import (
    AnalysisIntent,
    AnalysisIntentPolicy,
    AnalysisLimits,
    QueryExecutionPolicy,
    SQLSafetyPolicy,
)
from apps.queries.domain.value_objects import ChartType, FeedbackScore
from apps.users.domain.entities import Profile, User
from apps.users.domain.exceptions import InvalidEmailAddress, InvalidPhoneNumber
from apps.users.domain.value_objects import EmailAddress, PhoneNumber, UserType


def test_phone_number_accepts_only_exactly_ten_digits():
    assert str(PhoneNumber("0123456789")) == "0123456789"
    for invalid in ("", "123", "12345678901", "12345abcde", "+123456789"):
        with pytest.raises(InvalidPhoneNumber):
            PhoneNumber(invalid)


def test_email_value_object_requires_a_value_and_user_type_mapping_is_stable():
    with pytest.raises(InvalidEmailAddress):
        EmailAddress("")
    assert User(EmailAddress("a@example.com"), "A", "B").user_type_numeric == 1
    assert User(EmailAddress("admin@example.com"), "A", "B", user_type=UserType.ADMIN).user_type_numeric == 2


def test_profile_quota_is_informational_and_increment_is_immutable():
    profile = Profile(user_id=7, query_count=2, query_limit=2)
    incremented = profile.increment_query_count()
    assert profile.query_count == 2
    assert not profile.can_query
    assert incremented.query_count == 3
    assert not incremented.can_query


def test_dataset_ready_and_error_transitions_preserve_unrelated_metadata():
    dataset = Dataset(user_id=7, name="sales", file_path="sales.csv", error_msg="previous")
    ready = dataset.mark_ready({"tables": []}, 4, 2)
    assert ready.status is DatasetStatus.READY and ready.is_queryable
    assert (ready.row_count, ready.column_count, ready.error_msg) == (4, 2, "previous")
    assert dataset.status is DatasetStatus.PROCESSING
    failed = ready.mark_error("broken")
    assert failed.status is DatasetStatus.ERROR and failed.error_msg == "broken"
    assert (failed.schema_json, failed.row_count, failed.column_count) == (ready.schema_json, 4, 2)
    with pytest.raises(FrozenInstanceError):
        ready.status = DatasetStatus.ERROR


def test_dataset_ownership_policy_matches_dataset_owner():
    dataset = Dataset(id=3, user_id=2, name="orders", file_path="orders.csv")

    assert DatasetOwnershipPolicy.owns(dataset, 2)
    assert not DatasetOwnershipPolicy.owns(dataset, 8)


@pytest.mark.parametrize("status", [
    DatasetStatus.INACTIVE,
    DatasetStatus.ERROR,
    DatasetStatus.PROCESSING,
    DatasetStatus.UPLOADED,
])
def test_dataset_non_ready_states_are_not_queryable(status):
    with pytest.raises(DatasetNotQueryable):
        Dataset(user_id=1, name="x", file_path="x.csv", status=status).ensure_queryable()


def test_dataset_upload_policy_accepts_exact_size_limit_and_uppercase_extension():
    DatasetUploadPolicy.validate("VENTAS.CSV", DatasetUploadPolicy.MAX_FILE_SIZE_BYTES)


def test_dataset_upload_policy_rejects_size_above_limit_with_domain_details():
    size = DatasetUploadPolicy.MAX_FILE_SIZE_BYTES + 1
    with pytest.raises(DatasetFileTooLarge) as error:
        DatasetUploadPolicy.validate("ventas.csv", size)
    assert error.value.size_bytes == size
    assert error.value.max_size_bytes == DatasetUploadPolicy.MAX_FILE_SIZE_BYTES


def test_demo_session_expires_only_after_strictly_more_than_24_hours():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    session = DemoSession(SessionIdentifier("demo-1"), now, now)
    assert session.expires_at == now + DEMO_SESSION_TTL
    assert not session.is_expired(now + timedelta(hours=24))
    assert session.is_expired(now + timedelta(hours=24, microseconds=1))
    with pytest.raises(InvalidSessionIdentifier):
        SessionIdentifier("")
    with pytest.raises(InvalidSessionIdentifier):
        SessionIdentifier("x" * 37)


def test_query_history_result_and_feedback_keep_typed_values_and_defaults():
    history = QueryHistory(user_id=1, dataset_id=2, question="total?")
    result = QueryResult(query_id=9, chart_type=ChartType.BAR, result_json=[{"total": 3}])
    feedback = QueryFeedback(query_id=9, score=FeedbackScore.USEFUL, comment="ok")
    assert not history.success and not history.cached and history.retry_count == 0
    assert result.chart_type is ChartType.BAR and result.row_count == 0
    assert feedback.score is FeedbackScore.USEFUL


@pytest.mark.parametrize(("value", "expected"), [(1, FeedbackScore.USEFUL), (-1, FeedbackScore.NOT_USEFUL)])
def test_feedback_score_accepts_only_the_two_contract_values(value, expected):
    assert FeedbackScore.from_value(value) is expected


@pytest.mark.parametrize("value", [0, 2, -2, 100])
def test_feedback_score_rejects_other_values(value):
    with pytest.raises(InvalidFeedbackScore):
        FeedbackScore.from_value(value)


def test_project_status_entities_preserve_each_supported_status():
    assert ProjectPhase(order=1, name="Design", status=ProjectPhaseStatus.BLOCKED).status.value == "blocked"
    assert ProjectModule(order=1, name="Chat", status=ProjectModuleStatus.BETA).status.value == "beta"


def test_analysis_intent_policy_selects_matching_intent_and_returns_none_for_normal_query():
    assert AnalysisIntentPolicy.detect("pronóstico para el próximo trimestre") is AnalysisIntent.FORECAST
    assert AnalysisIntentPolicy.detect("encuentra anomalías") is AnalysisIntent.ANOMALY
    assert AnalysisIntentPolicy.detect("describe segmentos") is AnalysisIntent.SEGMENT
    assert AnalysisIntentPolicy.detect("qué explica las ventas") is AnalysisIntent.DRIVERS
    assert AnalysisIntentPolicy.detect("dame una descripción") is AnalysisIntent.SUMMARY
    assert AnalysisIntentPolicy.detect("ventas del último mes") is None


def test_query_execution_policy_defines_positive_attempt_and_row_limits():
    policy = QueryExecutionPolicy()
    assert (policy.max_attempts, policy.max_result_rows) == (3, 1000)
    assert QueryExecutionPolicy(max_attempts=1, max_result_rows=7).max_result_rows == 7


@pytest.mark.parametrize("kwargs", [
    {"max_attempts": 0},
    {"max_attempts": True},
    {"max_result_rows": -1},
    {"max_result_rows": 1.5},
])
def test_query_execution_policy_rejects_invalid_limits(kwargs):
    with pytest.raises(InvalidPolicyConfiguration):
        QueryExecutionPolicy(**kwargs)


def test_analysis_limits_validate_forecast_minimum_against_history_window():
    limits = AnalysisLimits()
    assert (limits.max_anomalies, limits.forecast_horizon) == (20, 6)
    assert (limits.min_anomaly_rows, limits.min_segment_rows) == (10, 8)
    with pytest.raises(InvalidPolicyConfiguration, match="min_forecast_periods"):
        AnalysisLimits(max_history_periods=5, min_forecast_periods=6)


@pytest.mark.parametrize(
    "field_name",
    ["min_anomaly_rows", "min_segment_rows"],
)
@pytest.mark.parametrize("value", [0, -1, True])
def test_analysis_limits_require_positive_integer_minimums(field_name, value):
    with pytest.raises(InvalidPolicyConfiguration, match=field_name):
        AnalysisLimits(**{field_name: value})


def test_sql_safety_policy_exposes_canonical_validator_contract():
    policy = SQLSafetyPolicy()
    assert policy.allowed_statement == "SELECT"
    assert {"DROP", "DELETE", "INSERT", "UPDATE", "ATTACH", "PRAGMA"}.issubset(
        policy.forbidden_operations
    )
    assert policy.allows_single_terminal_semicolon
    assert not policy.security_rejection_is_retryable
