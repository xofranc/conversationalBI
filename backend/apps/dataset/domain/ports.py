"""Contratos estructurales para coordinar recursos externos de datasets."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from .entities import Dataset


class DatasetFileStorage(Protocol):
    """Guarda y elimina el archivo fuente de un dataset."""

    def store(self, filename: str, content: bytes, user_id: int) -> str: ...

    def delete(self, file_path: str) -> None: ...


class DatasetSchemaExtractor(Protocol):
    """Extrae metadatos de schema desde un archivo fuente."""

    def extract(self, file_path: str) -> dict[str, Any]: ...


class DatasetMaterializer(Protocol):
    """Materializa y elimina la representación consultable de un dataset."""

    def materialize(self, dataset_id: int, file_path: str) -> str: ...

    def ensure_available(
        self, dataset_id: int, file_path: str, materialized_path: str
    ) -> str: ...

    def delete(self, materialized_path: str) -> None: ...


class DatasetDataReader(Protocol):
    """Lee datasets y sus tablas para consultas y análisis."""

    def get_dataset(self, dataset_id: int) -> Dataset: ...

    def read_tables(self, dataset: Dataset) -> Mapping[str, object]: ...

    def infer_dtype(self, series: object) -> str: ...


class DatasetResourceCleanup(Protocol):
    """Elimina recursos externos de un dataset propiedad del usuario.

    El contrato acepta identidades escalares para que tanto el ciclo de vida
    demo como la eliminación de datasets puedan delegar en la misma abstracción
    sin depender de casos de uso de application.
    """

    def delete(self, dataset_id: int, user_id: int) -> None: ...
