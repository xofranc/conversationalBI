"""Compatibility facade for user application use cases."""

from apps.users.application.dtos import CanAccessDatasetInput, GetQuotaInput


def _user_use_cases():
    from config.composition import build_user_use_cases

    return build_user_use_cases()


class UserService:
    @staticmethod
    def can_query(user) -> bool:
        return _user_use_cases()["get_quota"].execute(
            GetQuotaInput(user.pk)
        ).available

    @staticmethod
    def increment_usage(user) -> None:
        _user_use_cases()["increment_query_usage"].execute(user.pk)

    # ── Permisos sobre datasets ────────────────────────────────────────────
    @staticmethod
    def can_access_dataset(user, dataset_id: int) -> bool:
        return _user_use_cases()["can_access_dataset"].execute(
            CanAccessDatasetInput(user_id=user.pk, dataset_id=dataset_id)
        ).allowed
