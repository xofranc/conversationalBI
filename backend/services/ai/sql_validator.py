"""Legacy compatibility shim for the queries AI SQL validator."""

from apps.queries.infrastructure.ai.sql_validator import SecurityError
from apps.queries.infrastructure.ai.sql_validator import SQLValidator as _SQLValidator


class SQLValidator(_SQLValidator):
    """Preserve the former class-level API; validation stays in infrastructure."""

    @staticmethod
    def assert_safe(sql: str) -> None:
        _SQLValidator().assert_safe(sql)


__all__ = ["SecurityError", "SQLValidator"]
