from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from django.conf import settings

from apps.core.domain.entities import DemoSession
from apps.core.domain.value_objects import SessionIdentifier
from apps.core.infrastructure.models import DemoSession as SessionModel
from apps.core.infrastructure.repositories import DjangoDemoSessionRepository
from apps.dataset.domain.entities import Dataset, DatasetStatus, DatasetTable
from apps.dataset.domain.exceptions import DatasetOwnershipViolation
from apps.dataset.infrastructure.adapters import DjangoDatasetResourceCleanup
from apps.dataset.infrastructure.models import Dataset as DatasetModel
from apps.dataset.infrastructure.repositories import DjangoDatasetRepository, DjangoDatasetTableRepository
from apps.project_status.domain.entities import (
    ProjectModule,
    ProjectModuleStatus,
    ProjectPhase,
    ProjectPhaseStatus,
)
from apps.project_status.infrastructure.models import ProjectModule as ModuleModel
from apps.project_status.infrastructure.models import ProjectPhase as PhaseModel
from apps.project_status.infrastructure.repositories import DjangoProjectModuleRepository, DjangoProjectPhaseRepository
from apps.queries.domain.entities import QueryFeedback, QueryHistory, QueryResult
from apps.queries.domain.value_objects import ChartType, FeedbackScore
from apps.queries.infrastructure.models import QueryFeedback as FeedbackModel
from apps.queries.infrastructure.models import QueryHistory as HistoryModel
from apps.queries.infrastructure.models import QueryResult as ResultModel
from apps.queries.infrastructure.repositories import (
    DjangoQueryFeedbackRepository,
    DjangoQueryHistoryRepository,
    DjangoQueryResultRepository,
)
from apps.users.domain.entities import Profile, User
from apps.users.domain.value_objects import EmailAddress, PhoneNumber, UserType
from apps.users.infrastructure.models import Profile as ProfileModel
from apps.users.infrastructure.models import User as UserModel
from apps.users.infrastructure.repositories import DjangoProfileRepository, DjangoUserRepository


@pytest.fixture
def user():
    return get_user_model().objects.create_user(
        email="repository@example.com", password="secret", first_name="Test", last_name="Owner"
    )


@pytest.mark.django_db(transaction=True)
def test_dataset_repositories_round_trip_entities_and_stable_identity(user):
    datasets, tables = DjangoDatasetRepository(), DjangoDatasetTableRepository()
    saved = datasets.save(Dataset(
        user_id=user.pk, name="Sales", file_path="sales.csv", description="monthly",
        file_size=14, status=DatasetStatus.READY, schema_json={"tables": []}, row_count=4, column_count=2,
    ))
    assert saved.id and saved.user_id == user.pk and saved.status is DatasetStatus.READY
    updated = datasets.save(Dataset(
        id=saved.id, user_id=user.pk, name="Sales v2", file_path="sales.csv", status=DatasetStatus.ERROR,
        error_msg="bad file",
    ))
    assert updated.id == saved.id and updated.name == "Sales v2" and updated.error_msg == "bad file"
    assert datasets.get_by_id(saved.id) == updated
    assert datasets.list_by_user(user.pk) == (updated,)
    assert datasets.get_by_id(-1) is None

    table = tables.save(DatasetTable(dataset_id=saved.id, table_name="orders", row_count=4, column_count=2, columns_json=[{"name": "id"}]))
    same_table = tables.save(DatasetTable(dataset_id=saved.id, table_name="orders", row_count=5))
    assert same_table.id == table.id and same_table.row_count == 5
    assert tables.get_by_name(saved.id, "orders") == same_table
    assert tables.get_by_id(table.id) == same_table and len(tables.list_by_dataset(saved.id)) == 1
    tables.delete_for_dataset(saved.id)
    datasets.delete(saved.id)
    assert tables.get_by_id(table.id) is None and datasets.get_by_id(saved.id) is None


@pytest.mark.django_db(transaction=True)
def test_dataset_repository_delete_for_owner_deletes_dataset_for_matching_owner(user):
    dataset = DatasetModel.objects.create(
        user=user, name="Sales", file_path="sales.csv", status="ready"
    )
    repository = DjangoDatasetRepository()

    assert repository.delete_for_owner(dataset.pk, user.pk) is True
    assert not DatasetModel.objects.filter(pk=dataset.pk).exists()

@pytest.mark.django_db(transaction=True)
def test_dataset_repository_delete_for_owner_preserves_dataset_for_other_owner(user):
    other_user = get_user_model().objects.create_user(
        email="other-repository@example.com", password="secret"
    )
    dataset = DatasetModel.objects.create(
        user=user, name="Inventory", file_path="inventory.csv", status="ready"
    )
    repository = DjangoDatasetRepository()

    assert repository.delete_for_owner(dataset.pk, other_user.pk) is False
    assert DatasetModel.objects.filter(pk=dataset.pk, user_id=user.pk).exists()


@pytest.mark.django_db(transaction=True)
def test_dataset_repository_delete_for_owner_returns_false_for_missing_dataset(user):
    repository = DjangoDatasetRepository()

    assert repository.delete_for_owner(-1, user.pk) is False


def test_dataset_repository_delete_for_owner_uses_row_lock_inside_atomic(monkeypatch):
    from apps.dataset.infrastructure import repositories as dataset_repositories

    events = []
    transaction_state = {"in_atomic": False}

    class AtomicContext:
        def __enter__(self):
            transaction_state["in_atomic"] = True
            events.append("atomic_enter")

        def __exit__(self, exc_type, exc_value, traceback):
            events.append("atomic_exit")
            transaction_state["in_atomic"] = False

    model = SimpleNamespace(
        pk=41,
        user_id=7,
        name="Sales",
        description="",
        file_path="sales.csv",
        file_size=0,
        db_path="",
        schema_json={},
        row_count=0,
        column_count=0,
        status="ready",
        error_msg="",
        created_at=None,
        updated_at=None,
    )

    def delete_model():
        if not transaction_state["in_atomic"]:
            raise AssertionError("Dataset.delete() must run inside transaction.atomic()")
        events.append("delete")

    model.delete = delete_model
    queryset = Mock()
    queryset.first.side_effect = lambda: events.append("first") or model
    queryset.filter.side_effect = lambda **kwargs: events.append(("filter", kwargs)) or queryset
    manager = Mock()
    manager.select_for_update.side_effect = (
        lambda: events.append("select_for_update") or queryset
    )

    monkeypatch.setattr(
        dataset_repositories, "DatasetModel", SimpleNamespace(objects=manager)
    )
    monkeypatch.setattr(
        dataset_repositories,
        "transaction",
        SimpleNamespace(atomic=AtomicContext),
    )

    assert DjangoDatasetRepository().delete_for_owner(dataset_id=41, user_id=7) is True

    manager.select_for_update.assert_called_once_with()
    queryset.filter.assert_called_once_with(pk=41)
    assert events == [
        "atomic_enter",
        "select_for_update",
        ("filter", {"pk": 41}),
        "first",
        "delete",
        "atomic_exit",
    ]


@pytest.mark.django_db(transaction=True)
def test_resource_cleanup_rejects_owner_changed_before_conditional_delete(user):
    other_user = get_user_model().objects.create_user(
        email="changed-owner@example.com", password="secret"
    )
    dataset = DatasetModel.objects.create(
        user=user,
        name="Sales",
        file_path="sales.csv",
        db_path="db/sales",
        status="ready",
    )
    repository = DjangoDatasetRepository()
    file_storage, materializer = _RecordingDeleter(), _RecordingDeleter()

    class OwnerChangesBeforeDelete:
        def get_by_id(self, dataset_id):
            return repository.get_by_id(dataset_id)

        def delete_for_owner(self, dataset_id, user_id):
            DatasetModel.objects.filter(pk=dataset_id).update(user_id=other_user.pk)
            return repository.delete_for_owner(dataset_id, user_id)

    cleanup = DjangoDatasetResourceCleanup(
        OwnerChangesBeforeDelete(), file_storage, materializer
    )

    with pytest.raises(DatasetOwnershipViolation):
        cleanup.delete(dataset.pk, user.pk)

    assert DatasetModel.objects.filter(pk=dataset.pk, user_id=other_user.pk).exists()
    assert file_storage.deleted == []
    assert materializer.deleted == []


@pytest.mark.django_db(transaction=True)
def test_resource_cleanup_treats_concurrently_missing_dataset_as_noop(user):
    dataset = DatasetModel.objects.create(
        user=user,
        name="Sales",
        file_path="sales.csv",
        db_path="db/sales",
        status="ready",
    )
    repository = DjangoDatasetRepository()
    file_storage, materializer = _RecordingDeleter(), _RecordingDeleter()

    class DatasetDisappearsBeforeDelete:
        def get_by_id(self, dataset_id):
            return repository.get_by_id(dataset_id)

        def delete_for_owner(self, dataset_id, user_id):
            DatasetModel.objects.filter(pk=dataset_id).delete()
            return False

    cleanup = DjangoDatasetResourceCleanup(
        DatasetDisappearsBeforeDelete(), file_storage, materializer
    )

    cleanup.delete(dataset.pk, user.pk)

    assert not DatasetModel.objects.filter(pk=dataset.pk).exists()
    assert file_storage.deleted == []
    assert materializer.deleted == []


@pytest.mark.django_db(transaction=True)
def test_query_repositories_round_trip_history_result_and_feedback(user):
    dataset = DatasetModel.objects.create(user=user, name="Sales", file_path="sales.csv", status="ready")
    histories = DjangoQueryHistoryRepository()
    saved_history = histories.save(QueryHistory(
        user_id=user.pk, dataset_id=dataset.pk, question="Total sales?", sql_generated="SELECT 1",
        execution_time=0.5, success=True, model_used="unit-test", retry_count=2,
    ))
    assert saved_history.id and saved_history.success and saved_history.retry_count == 2
    changed_history = histories.save(QueryHistory(
        id=saved_history.id, user_id=user.pk, dataset_id=dataset.pk, question="Updated?", cached=True,
    ))
    assert changed_history.id == saved_history.id and changed_history.cached
    assert histories.get_by_id(saved_history.id) == changed_history
    assert histories.list_by_user(user.pk) == (changed_history,)
    assert histories.list_by_dataset(dataset.pk) == (changed_history,)

    results = DjangoQueryResultRepository()
    result = results.save(QueryResult(
        query_id=saved_history.id, result_json=[{"total": 9}], columns=[{"name": "total"}],
        row_count=1, answer="nine", chart_type=ChartType.BAR, chart_config={"color": "blue"},
    ))
    updated_result = results.save(QueryResult(
        id=result.id, query_id=saved_history.id, result_json=[{"total": 10}], chart_type=ChartType.LINE,
    ))
    assert updated_result.id == result.id and updated_result.chart_type is ChartType.LINE
    assert results.get_by_query_id(saved_history.id) == updated_result

    feedbacks = DjangoQueryFeedbackRepository()
    feedback = feedbacks.save(QueryFeedback(query_id=saved_history.id, score=FeedbackScore.USEFUL, comment="clear"))
    updated_feedback = feedbacks.save(QueryFeedback(
        id=feedback.id, query_id=saved_history.id, score=FeedbackScore.NOT_USEFUL, comment="changed",
    ))
    assert updated_feedback.id == feedback.id and updated_feedback.score is FeedbackScore.NOT_USEFUL
    assert feedbacks.get_by_query_id(saved_history.id) == updated_feedback


@pytest.mark.django_db(transaction=True)
def test_user_and_profile_repositories_map_identity_phone_entry_date_and_quota(user):
    users = DjangoUserRepository()
    entity = users.get_by_id(user.pk)
    assert entity == User(
        id=user.pk, email=EmailAddress(user.email), first_name="Test", last_name="Owner",
        is_active=True, user_type=UserType.USER,
    )
    updated_user = users.save(User(
        id=user.pk, email=EmailAddress(user.email), first_name="Updated", last_name="Owner",
        user_type=UserType.ADMIN,
    ))
    assert updated_user.user_type is UserType.ADMIN and users.get_by_email(updated_user.email) == updated_user
    new_user = users.save(User(EmailAddress("new@example.com"), "New", "User"))
    assert new_user.id and UserModel.objects.filter(pk=new_user.id).exists()

    profiles = DjangoProfileRepository()
    birth_date, entry_date = date(1990, 2, 3), date(2020, 4, 5)
    profile = profiles.save(Profile(
        user_id=user.pk, bio="bio", phone_number=PhoneNumber("1234567890"), birth_date=birth_date,
        entry_date=entry_date, query_count=4, query_limit=12,
    ))
    assert profile.id and profile.phone_number == PhoneNumber("1234567890")
    assert (profile.birth_date, profile.entry_date, profile.query_count) == (birth_date, entry_date, 4)
    assert profiles.phone_number_exists(PhoneNumber("1234567890"))
    assert not profiles.phone_number_exists(PhoneNumber("1234567890"), excluding_profile_id=profile.id)
    profiles.increment_query_count(user.pk)
    assert profiles.get_by_user_id(user.pk).query_count == 5
    profiles.increment_query_count(new_user.id)  # missing profile is lazily created
    assert profiles.get_by_user_id(new_user.id).query_count == 1


@pytest.mark.django_db(transaction=True)
def test_demo_session_and_project_repositories_preserve_values_and_expiry_boundary():
    now = datetime(2026, 3, 1, tzinfo=timezone.utc)
    sessions = DjangoDemoSessionRepository()
    session = sessions.save(DemoSession(SessionIdentifier("session-1"), now - timedelta(days=2), now - timedelta(hours=25)))
    assert session.session_id == SessionIdentifier("session-1")
    assert sessions.get_by_session_id(SessionIdentifier("session-1")) == session
    assert sessions.list_expired_before(now - timedelta(hours=24)) == (session,)
    sessions.delete(session.session_id)
    assert sessions.get_by_session_id(session.session_id) is None

    phases, modules = DjangoProjectPhaseRepository(), DjangoProjectModuleRepository()
    phase = phases.save(ProjectPhase(
        order=2, name="Roadmap", status=ProjectPhaseStatus.IN_PROGRESS, date_completed=date(2026, 1, 1),
        github_url="https://github.com/example/project", doc_url="https://example.com/docs",
    ))
    assert phases.get_by_id(phase.id) == phase and phases.list_all() == (phase,)
    module = modules.save(ProjectModule(order=1, name="Chat", status=ProjectModuleStatus.BETA, icon="chat"))
    assert modules.get_by_id(module.id) == module and modules.list_all() == (module,)
    phases.delete(phase.id)
    modules.delete(module.id)
    assert not phases.list_all() and not modules.list_all()


@pytest.mark.django_db
def test_django_model_registry_and_legacy_exports_point_to_infrastructure_models():
    from apps.core.models import DemoSession as LegacySession
    from apps.dataset.models import Dataset as LegacyDataset, DatasetTable as LegacyDatasetTable
    from apps.project_status.models import ProjectModule as LegacyModule, ProjectPhase as LegacyPhase
    from apps.queries.models import QueryFeedback as LegacyFeedback, QueryHistory as LegacyHistory, QueryResult as LegacyResult
    from apps.users.models import Profile as LegacyProfile, User as LegacyUser

    expected = {
        "core.DemoSession": (SessionModel, LegacySession),
        "dataset.Dataset": (DatasetModel, LegacyDataset),
        "dataset.DatasetTable": (DatasetModel._meta.apps.get_model("dataset", "DatasetTable"), LegacyDatasetTable),
        "queries.QueryHistory": (HistoryModel, LegacyHistory),
        "queries.QueryResult": (ResultModel, LegacyResult),
        "queries.QueryFeedback": (FeedbackModel, LegacyFeedback),
        "users.User": (UserModel, LegacyUser),
        "users.Profile": (ProfileModel, LegacyProfile),
        "project_status.ProjectPhase": (PhaseModel, LegacyPhase),
        "project_status.ProjectModule": (ModuleModel, LegacyModule),
    }
    for qualified_name, (model, legacy_export) in expected.items():
        app_label, model_name = qualified_name.split(".")
        assert apps.get_model(app_label, model_name) is model
        assert legacy_export is model


def test_auth_setting_and_retired_dataset_permission_legacy_shim_import():
    from apps.dataset import permissions as legacy_dataset_permissions

    assert settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] == [
        "apps.users.infrastructure.authentication.SupabaseAuth",
    ]
    assert legacy_dataset_permissions.__all__ == ()
    assert not hasattr(legacy_dataset_permissions, "IsDatasetOwner")


class _RecordingDeleter:
    def __init__(self):
        self.deleted = []

    def delete(self, path):
        self.deleted.append(path)
