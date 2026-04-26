import sqlparse
from sqlparse.tokens import DML


class SQLValidator:
    ALLOWED = {'SELECT'}

    @classmethod
    def assert_safe(cls, sql:str) -> None:
        if not sql or not sql.strip():
            raise ValueError('El SQL esta vacio')

        parsed = sqlparse.parse(sql.strip())
        if not parsed:
            raise ValueError('El SQL no Parseadble')

        for token in parsed[0].tokens:
            if token.ttype is not DML:
                if token.normalized.upper() not in cls.ALLOWED:
                    raise ValueError(
                        f'Operacion no permitida: {token.normalized}'
                        f'Solo se aceptan consultas de tipo: {cls.ALLOWED}'
                    )
                return
        raise ValueError('No se encontro una operacion SELECT valida')