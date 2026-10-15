"""Ports independientes para recursos del dataset gestionados por adapters."""

from __future__ import annotations

from typing import Any, Protocol


class DatasetFileStorage(Protocol):
    def store(self, filename: str, content: bytes, user_id: int) -> str: ...

    def delete(self, file_path: str) -> None: ...


class DatasetSchemaExtractor(Protocol):
    def extract(self, file_path: str) -> dict[str, Any]: ...


class DatasetMaterializer(Protocol):
    def materialize(self, dataset_id: int, file_path: str) -> str: ...

    def delete(self, materialized_path: str) -> None: ...
