import pytest

import json

import pytest

from apps.dataset.infrastructure.query_data_source import DatasetQueryDataSource
from apps.dataset.infrastructure.repositories import DjangoDatasetRepository
from apps.dataset.models import Dataset
from apps.queries.domain.policies import QueryExecutionPolicy
from apps.queries.infrastructure.ai.sql_executor import SQLExecutor
from conftest import requires_postgres

@pytest.fixture
def csv_dataset(test_user, tmp_path, settings, materialized_dataset):
    settings.MEDIA_ROOT = str(tmp_path)
    (tmp_path / "sales.csv").write_text(
        "city,amount\nBogota,100.5\nCali,200.0\nMedellin,150.0\nCali,80.0\nBogota,300.0\n"
    )
    dataset = Dataset.objects.create(
        user=test_user,
        name="sales",
        file_path="sales.csv",
        status=Dataset.Status.READY,
        schema_json={"tables": [{"name": "main", "row_count": 5, "columns": []}]},
    )
    return materialized_dataset(dataset)


def _real_executor(max_result_rows=1000):
    source = DatasetQueryDataSource(DjangoDatasetRepository())
    return SQLExecutor(source, QueryExecutionPolicy(max_result_rows=max_result_rows))

class FakeDataSource:
    def __init__(self):
        self.dataset = object()
        self.lookups = []
        self.executions = []

    def get_dataset(self, dataset_id):
        self.lookups.append(dataset_id)
        return self.dataset

    def execute_sql(self, dataset, sql):
        self.executions.append((dataset, sql))
        return ([{"value": 1}], [{"name": "value", "dtype": "int"}])


def test_run_uses_injected_data_source_and_applies_policy_row_limit():
    source = FakeDataSource()
    executor = SQLExecutor(source, QueryExecutionPolicy(max_result_rows=7))

    rows, columns = executor.run("  SELECT value FROM data;  ", 23)

    assert source.lookups == [23]
    assert source.executions == [(source.dataset, "SELECT * FROM (SELECT value FROM data) LIMIT 7")]
    assert rows == [{"value": 1}]
    assert columns == [{"name": "value", "dtype": "int"}]


def test_run_preserves_inner_limit_while_enforcing_outer_policy_limit():
    source = FakeDataSource()
    executor = SQLExecutor(source, QueryExecutionPolicy(max_result_rows=10))

    executor.run("SELECT value FROM data LIMIT 2", 5)

    assert source.executions[0][1] == (
        "SELECT * FROM (SELECT value FROM data LIMIT 2) LIMIT 10"
    )


def test_run_wraps_data_source_errors_as_execution_errors():
    class BrokenSource:
        def get_dataset(self, dataset_id):
            raise LookupError(f"missing dataset {dataset_id}")

    with pytest.raises(ValueError, match="Error ejecutando SQL: missing dataset 404"):
        SQLExecutor(BrokenSource()).run("SELECT 1", 404)


@requires_postgres
@pytest.mark.django_db
class TestSqlExecutorPostgresIntegration:
    def test_query_without_inner_limit_is_bounded_by_domain_policy(self, csv_dataset):
        rows, _columns = _real_executor(max_result_rows=2).run(
            "SELECT * FROM main", csv_dataset.id,
        )
        assert len(rows) == 2

    def test_inner_limit_above_policy_does_not_bypass_outer_limit(self, csv_dataset):
        rows, _columns = _real_executor(max_result_rows=2).run(
            "SELECT * FROM main LIMIT 999", csv_dataset.id,
        )
        assert len(rows) == 2

    def test_inner_limit_below_policy_is_preserved(self, csv_dataset):
        rows, _columns = _real_executor(max_result_rows=2).run(
            "SELECT * FROM main LIMIT 1", csv_dataset.id,
        )
        assert len(rows) == 1

    def test_column_name_containing_limit_does_not_change_limit_behavior(self, csv_dataset):
        rows, _columns = _real_executor(max_result_rows=10).run(
            "SELECT city, amount FROM main ORDER BY amount DESC", csv_dataset.id,
        )
        assert len(rows) == 5 and rows[0]["amount"] == 300.0

    def test_json_dataset_tables_remain_queryable(self, test_user, tmp_path, settings, materialized_dataset):
        settings.MEDIA_ROOT = str(tmp_path)
        (tmp_path / "store.json").write_text(json.dumps({
            "sales": [{"city": "Bogota", "amount": 100}, {"city": "Cali", "amount": 50}],
            "products": [{"name": "A", "price": 10}],
        }))
        dataset = Dataset.objects.create(
            user=test_user,
            name="store",
            file_path="store.json",
            status=Dataset.Status.READY,
            schema_json={"tables": [
                {"name": "sales", "row_count": 2, "columns": []},
                {"name": "products", "row_count": 1, "columns": []},
            ]},
        )
        dataset = materialized_dataset(dataset)
        executor = _real_executor()

        sales, _ = executor.run("SELECT * FROM sales WHERE city = 'Cali'", dataset.id)
        products, _ = executor.run("SELECT name FROM products", dataset.id)
        assert sales == [{"city": "Cali", "amount": 50}]
        assert products == [{"name": "A"}]
