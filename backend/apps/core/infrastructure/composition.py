"""Composition root de sesiones demo."""

from typing import cast

from apps.core.application.use_cases import (
    CleanupDemoSession,
    CleanupExpiredDemoSessions,
    GetOrCreateDemoSession,
    GetOrCreateDemoUser,
    ListDemoSessionDatasets,
)
from apps.dataset.application.use_cases import DeleteDataset
from apps.dataset.infrastructure.composition import build_dataset_use_cases
from apps.users.infrastructure.repositories import DjangoUserRepository

from .adapters import DjangoClock, DjangoDemoDatasetLifecycle
from .repositories import DjangoDemoSessionRepository


def build_core_use_cases() -> dict[str, object]:
    sessions = DjangoDemoSessionRepository()
    clock = DjangoClock()
    get_user = GetOrCreateDemoUser(DjangoUserRepository())
    delete_dataset = cast(DeleteDataset, build_dataset_use_cases()["delete"])
    lifecycle = DjangoDemoDatasetLifecycle(delete_dataset)
    cleanup = CleanupDemoSession(get_user, lifecycle)
    return {
        "get_or_create_session": GetOrCreateDemoSession(sessions, clock),
        "get_or_create_user": get_user,
        "list_datasets": ListDemoSessionDatasets(get_user, lifecycle),
        "cleanup_session": cleanup,
        "cleanup_expired_sessions": CleanupExpiredDemoSessions(sessions, cleanup, clock),
        "sessions": sessions,
    }
