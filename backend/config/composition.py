"""Application composition root: build adapters and inject them into HTTP routes."""

from apps.core.infrastructure.composition import (
    build_core_use_cases as _build_core_use_cases,
)
from apps.core.interfaces.urls import create_urlpatterns as create_core_urlpatterns
from apps.dataset.infrastructure.composition import (
    build_dataset_use_cases as _build_dataset_use_cases,
)
from apps.dataset.interfaces.urls import create_urlpatterns as create_dataset_urlpatterns
from apps.project_status.infrastructure.composition import (
    build_project_status_use_cases as _build_project_status_use_cases,
)
from apps.project_status.interfaces.urls import (
    create_urlpatterns as create_project_status_urlpatterns,
)
from apps.queries.infrastructure.composition import (
    build_query_use_cases as _build_query_use_cases,
)
from apps.queries.interfaces.urls import create_urlpatterns as create_query_urlpatterns
from apps.users.infrastructure.composition import (
    build_user_use_cases as _build_user_use_cases,
)
from apps.users.interfaces.urls import create_urlpatterns as create_user_urlpatterns


def build_interface_urlpatterns():
    """Build each use-case bundle once and inject it into its module's routes."""
    core_use_cases = _build_core_use_cases()
    return {
        "project_status": create_project_status_urlpatterns(
            _build_project_status_use_cases()
        ),
        "users": create_user_urlpatterns(_build_user_use_cases()),
        "dataset": create_dataset_urlpatterns(
            _build_dataset_use_cases(), core_use_cases
        ),
        "queries": create_query_urlpatterns(
            _build_query_use_cases(), core_use_cases
        ),
        "core": create_core_urlpatterns(core_use_cases),
    }


def build_core_use_cases():
    return _build_core_use_cases()


def build_dataset_use_cases():
    return _build_dataset_use_cases()


def build_query_use_cases():
    return _build_query_use_cases()


def build_user_use_cases():
    return _build_user_use_cases()


def build_core_urlpatterns():
    return create_core_urlpatterns(_build_core_use_cases())


def build_cleanup_expired_sessions_use_case():
    """Compose the core cleanup use case for non-HTTP entry points."""
    return build_core_use_cases()["cleanup_expired_sessions"]


def build_dataset_urlpatterns():
    return create_dataset_urlpatterns(
        _build_dataset_use_cases(), _build_core_use_cases()
    )


def build_project_status_urlpatterns():
    return create_project_status_urlpatterns(_build_project_status_use_cases())


def build_query_urlpatterns():
    return create_query_urlpatterns(
        _build_query_use_cases(), _build_core_use_cases()
    )


def build_user_urlpatterns():
    return create_user_urlpatterns(_build_user_use_cases())
