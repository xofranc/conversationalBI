# services/ai/tests/test_sql_validator.py
import pytest

from services.ai.sql_validator import SecurityError, SQLValidator


class TestSQlValido:

    def test_select_simple_ok(self):
        SQLValidator.assert_safe('SELECT * FROM ventas')

    def test_select_con_agregacion_ok(self):
        SQLValidator.assert_safe(
            'SELECT region, SUM(monto) FROM ventas GROUP BY region'
        )


class TestSQLPeligroso:
    """Todo SQL rechazado lanza SecurityError (fail-fast, no reintentable)."""

    @pytest.mark.parametrize('sql', [
        'DROP TABLE ventas',
        'DELETE FROM ventas',
        'INSERT INTO ventas VALUES (1)',
        'UPDATE ventas SET monto = 0',
        'SELECT * FROM ventas UNION SELECT * FROM users',
        'SELECT * FROM ventas; SELECT * FROM users',
        'ATTACH DATABASE "otra.db" AS otra',
        'PRAGMA table_info(ventas)',
        'ALTER TABLE ventas ADD COLUMN x INT',
        '',
        '   ',
    ])
    def test_rechazado_con_security_error(self, sql):
        with pytest.raises(SecurityError):
            SQLValidator.assert_safe(sql)
