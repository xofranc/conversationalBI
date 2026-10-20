"""Acceso de lectura a los datos materializados para los motores de consulta."""

from __future__ import annotations

import pandas as pd

from apps.dataset.domain.entities import Dataset
from apps.dataset.domain.repositories import DatasetRepository
from .database_service import DatabaseService
from .schema_service import SchemaService


class DatasetQueryDataSource:
    """Resuelve datasets y lee SQL/tablas sin exponer persistencia al motor."""

    def __init__(self, datasets: DatasetRepository) -> None:
        self._datasets = datasets

    def get_dataset(self, dataset_id: int) -> Dataset:
        dataset = self._datasets.get_by_id(dataset_id)
        if dataset is None:
            raise ValueError(f"No existe el dataset {dataset_id}")
        return dataset

    def execute_sql(self, dataset: Dataset, sql: str) -> tuple[list, list]:
        """Ejecuta SQL read-only y normaliza los datos antes de salir de infra."""
        conn = DatabaseService.connect_readonly(dataset.db_path)
        try:
            frame = pd.read_sql_query(sql, conn)
        finally:
            conn.close()

        columns = [
            {"name": column, "dtype": SchemaService.infer_dtype(frame[column])}
            for column in frame.columns
        ]
        rows = [
            {key: self._json_safe(value) for key, value in row.items()}
            for row in frame.to_dict(orient="records")
        ]
        return rows, columns

    def read_tables(self, dataset: Dataset) -> dict:
        """Devuelve las tablas materializadas para el motor estadístico."""
        return DatabaseService.read_tables(dataset.db_path)

    @staticmethod
    def infer_dtype(series: pd.Series) -> str:
        """Infiere el tipo de una serie usando el servicio concreto del dataset."""
        return SchemaService.infer_dtype(series)

    @staticmethod
    def _json_safe(value):
        if value is None or pd.isna(value):
            return None
        if hasattr(value, "isoformat"):
            return value.isoformat()
        if hasattr(value, "item"):
            return value.item()
        return value
