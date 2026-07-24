import re
import sqlparse
from sqlparse.tokens import DML, Keyword


class SecurityError(Exception):
    """SQL rechazado por políticas de seguridad. No reintentable: fail-fast."""


class SQLValidator:
    ALLOWED = {'SELECT'}

    BLOCKED_PATTERNS = [
        r';',                    # Multi-statement
        r'\bUNION\b',            # UNION injection
        r'\bATTACH\b',           # Attach database
        r'\bDETACH\b',
        r'\bPRAGMA\b',           # SQLite pragma
        r'\bload_extension\b',   # SQLite extensions
        r'\bCREATE\b',
        r'\bINSERT\b',
        r'\bUPDATE\b',
        r'\bDELETE\b',
        r'\bDROP\b',
        r'\bALTER\b',
        r'\bTRUNCATE\b',
        r'\bREPLACE\b',
    ]

    @classmethod
    def assert_safe(cls, sql: str) -> None:
        if not sql or not sql.strip():
            raise SecurityError('El SQL está vacío')

        # 1. Bloquear patrones peligrosos
        sql_upper = sql.upper()
        for pattern in cls.BLOCKED_PATTERNS:
            if re.search(pattern, sql_upper):
                raise SecurityError(
                    'Operación no permitida. Solo se aceptan consultas SELECT simples.'
                )

        # 2. Parsear y verificar que sea SELECT
        parsed = sqlparse.parse(sql.strip())
        if not parsed:
            raise SecurityError('SQL no parseable')

        statement = parsed[0]
        first_token = statement.token_first(skip_cm=True, skip_ws=True)

        if first_token is None:
            raise SecurityError('No se encontró operación válida')

        if first_token.ttype is DML:
            if first_token.normalized.upper() not in cls.ALLOWED:
                raise SecurityError(f'Operación no permitida: {first_token.normalized}')
        elif first_token.ttype is Keyword:
            if first_token.normalized.upper() not in cls.ALLOWED:
                raise SecurityError(f'Operación no permitida: {first_token.normalized}')
        else:
            raise SecurityError('No se encontró una operación SELECT válida')