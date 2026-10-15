import pytest

from apps.queries.domain.policies import SQLSafetyPolicy
from apps.queries.infrastructure.ai.sql_validator import SecurityError, SQLValidator


def test_validator_accepts_select_and_a_single_terminal_semicolon():
    validator = SQLValidator(SQLSafetyPolicy())
    validator.assert_safe("SELECT region, SUM(amount) FROM sales GROUP BY region;")
    validator.assert_safe("SELECT * FROM sales\n")


@pytest.mark.parametrize("operation", SQLSafetyPolicy().forbidden_operations)
def test_validator_consumes_domain_policy_forbidden_operations(operation):
    validator = SQLValidator(SQLSafetyPolicy())

    with pytest.raises(SecurityError):
        validator.assert_safe(f"{operation} TABLE sales")


@pytest.mark.parametrize("sql", [
    "SELECT * FROM sales UNION SELECT * FROM users",
    "SELECT * FROM sales; SELECT * FROM users",
    "",
    "   ",
])
def test_validator_rejects_multiple_statements_empty_or_unsafe_selects(sql):
    with pytest.raises(SecurityError):
        SQLValidator(SQLSafetyPolicy()).assert_safe(sql)
