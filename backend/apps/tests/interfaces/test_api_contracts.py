from types import SimpleNamespace

import pytest
from django.test import override_settings
from django.urls import include, path
from rest_framework.test import APIClient

from apps.core.application.dtos import (
    CleanupSessionResultDTO,
    DemoUserDTO,
)
from apps.core.interfaces.identity import request_identity
from apps.core.interfaces.permissions import IsAuthenticatedOrDemo
from apps.core.interfaces.urls import create_urlpatterns as core_urls
from apps.dataset.application.dtos import DatasetDTO
from apps.dataset.application.use_cases import DatasetAccessDenied, DatasetUploadRejected
from apps.dataset.domain.exceptions import DatasetFileTooLarge, UnsupportedDatasetFileExtension
from apps.dataset.domain.policies import DatasetUploadPolicy
from apps.dataset.interfaces.urls import create_urlpatterns as dataset_urls
from apps.project_status.application.dtos import (
    ProjectModuleDTO,
    ProjectPhaseDTO,
    ProjectStatusDTO,
)
from apps.project_status.interfaces.urls import create_urlpatterns as project_urls
from apps.queries.application.dtos import (
    FeedbackDTO,
    QueryDetailDTO,
    QueryHistoryItemDTO,
    QueryResponseDTO,
)
from apps.queries.application.use_cases import (
    DatasetNotReady,
    FeedbackAlreadyExists,
    InvalidFeedbackScoreInput,
    QueryNotFound,
)
from apps.queries.interfaces.urls import create_urlpatterns as query_urls
from apps.users.application.dtos import ProfileDTO
from apps.users.interfaces.urls import create_urlpatterns as user_urls


STATE = {}


class UseCase:
    def __init__(self, name):
        self.name = name

    def execute(self, *args):
        return STATE[self.name](*args)


def use_cases(**state_names):
    """Map the exact names consumed by each view to state-backed handlers."""
    return {name: UseCase(state_name) for name, state_name in state_names.items()}


CORE = use_cases(get_or_create_user="get_or_create_user", cleanup_session="cleanup_session")
DATASET = use_cases(
    create="create_dataset", list="list_datasets", get="get_dataset", delete="delete_dataset",
)
QUERIES = use_cases(
    execute="execute_query", list_history="list_history",
    get_detail="get_detail", submit_feedback="submit_feedback",
)
USERS = use_cases(get_profile="get_profile", update_profile="update_profile")
PROJECT = use_cases(get_status="get_status")

identity_provider = lambda request: request_identity(request, CORE)

urlpatterns = [
    path("api/v1/core/", include(core_urls(CORE))),
    path(
        "api/v1/dataset/",
        include(
            dataset_urls(
                DATASET,
                identity_provider=identity_provider,
                permission_class=IsAuthenticatedOrDemo,
            )
        ),
    ),
    path(
        "api/v1/queries/",
        include(
            query_urls(
                QUERIES,
                identity_provider=identity_provider,
                permission_class=IsAuthenticatedOrDemo,
            )
        ),
    ),
    path("api/v1/users/", include(user_urls(USERS))),
    path("api/v1/project-status/", include(project_urls(PROJECT))),
]


def dataset_dto(**updates):
    fields = dict(
        id=12, user_id=41, name="Sales", description="monthly", file_size=5,
        schema={"tables": []}, row_count=2, column_count=1, status="ready",
        error_message="", created_at=None, updated_at=None, tables=(),
    )
    fields.update(updates)
    return DatasetDTO(**fields)


def query_response(**updates):
    fields = dict(
        query_id=3, sql="SELECT 1", success=True, error_message="", execution_time=0.1,
        model_used="test", retry_count=0, cached=False, data=({"n": 1},), columns=(),
        chart_type="table", chart_config={}, row_count=1, answer="one", suggestions=(),
    )
    fields.update(updates)
    return QueryResponseDTO(**fields)


def reset_state():
    def not_ready(_request):
        raise DatasetNotReady("El dataset no está listo para consultar")

    def missing_feedback(_request):
        raise QueryNotFound("not found")

    def duplicate_feedback(_request):
        raise FeedbackAlreadyExists("duplicate")

    def create_dataset(request):
        try:
            DatasetUploadPolicy.validate(request.filename, len(request.content))
        except (DatasetFileTooLarge, UnsupportedDatasetFileExtension) as error:
            raise DatasetUploadRejected(str(error)) from error
        return dataset_dto(name=request.name, file_size=len(request.content))

    STATE.clear()
    STATE.update({
        "get_or_create_user": lambda _request: DemoUserDTO(user_id=41, email="demo@test.local"),
        "cleanup_session": lambda _request: CleanupSessionResultDTO(deleted_dataset_count=2),
        "create_dataset": create_dataset,
        "list_datasets": lambda _request: (dataset_dto(),),
        "get_dataset": lambda _request: dataset_dto(),
        "delete_dataset": lambda _request: None,
        "execute_query": lambda _request: query_response(),
        "list_history": lambda _request: (),
        "get_detail": lambda _request: QueryDetailDTO(
            query_id=3, question="How many?", sql="SELECT 1", execution_time=0.1,
            success=True, error_message="", model_used="test", retry_count=0,
            cached=False, created_at=None, result=None,
        ),
        "submit_feedback": lambda _request: FeedbackDTO(query_id=3, score=1, comment="good", created_at=None),
        "get_profile": lambda _request: ProfileDTO(user_id=41, bio="", phone_number=None, birth_date=None, entry_date=None),
        "update_profile": lambda _request: ProfileDTO(user_id=41, bio="updated", phone_number=None, birth_date=None, entry_date=None),
        "get_status": lambda: ProjectStatusDTO(
            phases=(ProjectPhaseDTO(1, 1, "Build", "", "completed", None, "", ""),),
            modules=(ProjectModuleDTO(2, 1, "Chat", "", "live", "chat"),),
        ),
    })
    # Keep the failure responders available to tests without mocking legacy services.
    STATE["_not_ready"] = not_ready
    STATE["_missing_feedback"] = missing_feedback
    STATE["_duplicate_feedback"] = duplicate_feedback


@pytest.fixture(autouse=True)
def api_setup():
    reset_state()
    with override_settings(ROOT_URLCONF=__name__, REST_FRAMEWORK={
        "DEFAULT_AUTHENTICATION_CLASSES": [],
        "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
        "DEFAULT_THROTTLE_CLASSES": [],
        "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
        "PAGE_SIZE": 20,
    }):
        yield


@pytest.fixture
def client():
    return APIClient()


def test_dataset_routes_list_upload_and_invalid_upload_contract(client):
    headers = {"HTTP_X_SESSION_ID": "session-1"}
    listed = client.get("/api/v1/dataset/", **headers)
    assert listed.status_code == 200 and listed.json()[0]["status"] == "ready"
    detail = client.get("/api/v1/dataset/12/", **headers)
    assert detail.status_code == 200 and detail.json()["owner"] == "demo@test.local"
    schema = client.get("/api/v1/dataset/12/schema/", **headers)
    assert schema.status_code == 200 and schema.json()["schema_json"] == {"tables": []}

    # Use a real multipart upload for parser/serializer contract.
    from django.core.files.uploadedfile import SimpleUploadedFile
    uploaded = client.post(
        "/api/v1/dataset/",
        {"name": "Sales", "file": SimpleUploadedFile("sales.csv", b"id\n1", content_type="text/csv")},
        format="multipart",
        **headers,
    )
    assert uploaded.status_code == 201
    assert uploaded.json()["owner"] == "demo@test.local"
    assert uploaded.json()["schema_json"] == {"tables": []}

    rejected = client.post(
        "/api/v1/dataset/",
        {"name": "Sales", "file": SimpleUploadedFile("sales.exe", b"bad", content_type="application/x-msdownload")},
        format="multipart",
        **headers,
    )
    assert rejected.status_code == 400
    assert client.get("/api/v1/dataset/").status_code == 403
    assert client.delete("/api/v1/dataset/12/", **headers).status_code == 204

    ownership_checks = []

    def deny_dataset_access(request):
        ownership_checks.append(request.user_id)
        raise DatasetAccessDenied("not the owner")

    STATE["get_dataset"] = deny_dataset_access
    denied = client.get("/api/v1/dataset/12/", **headers)
    assert denied.status_code == 404
    assert ownership_checks == [41]


def test_demo_permission_only_checks_authentication_or_session_header():
    from django.test import RequestFactory

    permission = IsAuthenticatedOrDemo()
    factory = RequestFactory()
    anonymous = factory.get("/api/v1/dataset/")
    anonymous.user = SimpleNamespace(is_authenticated=False)
    assert not permission.has_permission(anonymous, None)

    demo = factory.get("/api/v1/dataset/", HTTP_X_SESSION_ID="session-1")
    demo.user = SimpleNamespace(is_authenticated=False)
    assert permission.has_permission(demo, None)
    assert demo.demo_session_id == "session-1"

    authenticated = factory.get("/api/v1/dataset/")
    authenticated.user = SimpleNamespace(is_authenticated=True)
    assert permission.has_permission(authenticated, None)

    # Object ownership is intentionally checked by application use cases.
    assert "has_object_permission" not in IsAuthenticatedOrDemo.__dict__
    from apps.dataset import permissions as legacy_dataset_permissions

    assert not hasattr(legacy_dataset_permissions, "IsDatasetOwner")


def test_query_route_success_not_ready_400_history_pagination_and_feedback_contract(client):
    headers = {"HTTP_X_SESSION_ID": "session-1"}
    response = client.post("/api/v1/queries/", {"dataset_id": 12, "question": "How many rows?"}, format="json", **headers)
    assert response.status_code == 200 and response.json()["query_id"] == 3
    assert response.json()["data"] == [{"n": 1}]

    STATE["execute_query"] = STATE["_not_ready"]
    bad_state = client.post("/api/v1/queries/", {"dataset_id": 12, "question": "How many rows?"}, format="json", **headers)
    assert bad_state.status_code == 400 and "error" in bad_state.json()
    STATE["execute_query"] = lambda _request: (_ for _ in ()).throw(RuntimeError("SECRET_TRACE"))
    internal = client.post("/api/v1/queries/", {"dataset_id": 12, "question": "How many rows?"}, format="json", **headers)
    assert internal.status_code == 500
    assert "SECRET_TRACE" not in str(internal.json())
    STATE["execute_query"] = lambda _request: query_response()

    STATE["list_history"] = lambda _request: tuple(
        QueryHistoryItemDTO(i, f"Question {i}", True, 0.1, "test", 0, False, None)
        for i in range(1, 24)
    )
    history = client.get("/api/v1/queries/?dataset_id=12", **headers)
    assert history.status_code == 200
    assert (history.json()["count"], len(history.json()["results"])) == (23, 20)
    assert history.json()["next"].endswith("?dataset_id=12&page=2")

    detail = client.get("/api/v1/queries/3/", **headers)
    assert detail.status_code == 200 and detail.json()["sql_generated"] == "SELECT 1"
    feedback = client.post("/api/v1/queries/3/feedback/", {"score": 1, "comment": "good"}, format="json", **headers)
    assert feedback.status_code == 201
    negative_feedback = client.post(
        "/api/v1/queries/3/feedback/", {"score": -1}, format="json", **headers,
    )
    assert negative_feedback.status_code == 201
    STATE["submit_feedback"] = STATE["_duplicate_feedback"]
    duplicate = client.post("/api/v1/queries/3/feedback/", {"score": -1}, format="json", **headers)
    assert duplicate.status_code == 400
    STATE["submit_feedback"] = STATE["_missing_feedback"]
    missing = client.post("/api/v1/queries/404/feedback/", {"score": 1}, format="json", **headers)
    assert missing.status_code == 404

    submitted_scores = []
    def invalid_feedback_score(request):
        submitted_scores.append(request.score)
        raise InvalidFeedbackScoreInput("El feedback debe ser útil o no útil")

    STATE["submit_feedback"] = invalid_feedback_score
    for score in (0, 7):
        invalid_score = client.post(
            "/api/v1/queries/3/feedback/", {"score": score}, format="json", **headers,
        )
        assert invalid_score.status_code == 400
        assert invalid_score.json() == {"score": ["El feedback debe ser útil o no útil"]}
    assert submitted_scores == [0, 7]  # IntegerField acepta; el caso de uso delega el rechazo al dominio.
    assert client.post("/api/v1/queries/", {"dataset_id": 12, "question": "x"}, format="json", **headers).status_code == 400


def test_profile_requires_auth_and_validates_phone_contract(client):
    assert client.get("/api/v1/users/profile/").status_code == 403
    client.force_authenticate(user=SimpleNamespace(pk=41, is_authenticated=True))
    profile = client.get("/api/v1/users/profile/")
    assert profile.status_code == 200 and profile.json()["user_id"] == 41
    updated = client.patch("/api/v1/users/profile/", {"bio": "updated"}, format="json")
    assert updated.status_code == 200 and updated.json()["bio"] == "updated"
    invalid = client.patch("/api/v1/users/profile/", {"phone_number": "123"}, format="json")
    assert invalid.status_code == 400 and "phone_number" in invalid.json()


def test_project_status_and_demo_cleanup_routes_return_contracts(client):
    status = client.get("/api/v1/project-status/")
    assert status.status_code == 200
    assert status.json()["project_name"] == "ConversationalBI"
    assert status.json()["phases"][0]["status"] == "completed"
    assert client.delete("/api/v1/core/session/").status_code == 400
    cleanup = client.delete("/api/v1/core/session/", HTTP_X_SESSION_ID="session-1")
    assert cleanup.status_code == 200
    assert cleanup.json() == {"message": "Se eliminaron 2 datasets"}
