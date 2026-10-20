"""Ejecución limitada de SQL contra el data source de datasets."""

from apps.queries.domain.policies import QueryExecutionPolicy


class SQLExecutor:
    def __init__(self, data_source, policy: QueryExecutionPolicy | None = None):
        self.data_source = data_source
        self.policy = policy or QueryExecutionPolicy()

    def run(self, sql: str, dataset_id: int) -> tuple[list[dict], list[dict]]:
        bounded_sql = sql.strip().rstrip(";")
        bounded_sql = f"SELECT * FROM ({bounded_sql}) LIMIT {self.policy.max_result_rows}"
        try:
            dataset = self.data_source.get_dataset(dataset_id)
            return self.data_source.execute_sql(dataset, bounded_sql)
        except Exception as exc:
            raise ValueError(f"Error ejecutando SQL: {exc}") from exc
