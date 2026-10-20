"""Compatibility facade for demo-session application use cases."""

from apps.core.application.dtos import DemoSessionInput


def _core_use_cases():
    from config.composition import build_core_use_cases

    return build_core_use_cases()


class DemoService:
    @staticmethod
    def get_or_create_session(session_id: str):
        return _core_use_cases()["get_or_create_session"].execute(
            DemoSessionInput(session_id)
        )

    @staticmethod
    def get_demo_user(session_id: str):
        return _core_use_cases()["get_or_create_user"].execute(
            DemoSessionInput(session_id)
        )

    @staticmethod
    def get_session_datasets(session_id: str):
        return _core_use_cases()["list_datasets"].execute(DemoSessionInput(session_id))

    @staticmethod
    def cleanup_session(session_id: str):
        result = _core_use_cases()["cleanup_session"].execute(
            DemoSessionInput(session_id)
        )
        return result.deleted_dataset_count

    @staticmethod
    def cleanup_all_expired():
        result = _core_use_cases()["cleanup_expired_sessions"].execute()
        return result.deleted_dataset_count
