"""Composition root para casos de uso de usuarios."""

from apps.dataset.infrastructure.repositories import DjangoDatasetRepository
from apps.users.application.use_cases import (
    AuthenticateExternalIdentity,
    CanAccessDataset,
    GetProfile,
    GetQuota,
    IncrementQueryUsage,
    UpdateProfile,
)

from .adapters import SupabaseAuthenticator
from .repositories import DjangoProfileRepository, DjangoUserRepository


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
