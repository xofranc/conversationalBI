"""Validación sintáctica/técnica SQL aplicando la política del dominio."""

import re

import sqlparse
from sqlparse.tokens import DML, Keyword

from apps.queries.domain.policies import SQLSafetyPolicy


class SecurityError(Exception):
    """SQL rechazado por la política de seguridad."""


class SQLValidator:
    def __init__(self, policy: SQLSafetyPolicy | None = None):
        self.policy = policy or SQLSafetyPolicy()

    def assert_safe(self, sql: str) -> None:
        if not sql or not sql.strip():
            raise SecurityError("El SQL está vacío")

        normalized = sql.strip()
        if normalized.endswith(";") and self.policy.allows_single_terminal_semicolon:
            normalized = normalized[:-1].strip()
        if ";" in normalized:
            raise SecurityError("Operación no permitida. Solo se aceptan consultas SELECT simples.")

        sql_upper = normalized.upper()
        for operation in self.policy.forbidden_operations:
            pattern = rf"\b{re.escape(operation.upper())}\b"
            if re.search(pattern, sql_upper):
                raise SecurityError(
                    "Operación no permitida. Solo se aceptan consultas SELECT simples."
                )

        parsed = sqlparse.parse(normalized)
        if not parsed:
            raise SecurityError("SQL no parseable")
        first_token = parsed[0].token_first(skip_cm=True, skip_ws=True)
        if first_token is None:
            raise SecurityError("No se encontró operación válida")
        if first_token.ttype in (DML, Keyword):
            if first_token.normalized.upper() != self.policy.allowed_statement.upper():
                raise SecurityError(f"Operación no permitida: {first_token.normalized}")
        else:
            raise SecurityError("No se encontró una operación SELECT válida")
