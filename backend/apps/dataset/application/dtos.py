"""DTOs de entrada y salida de la aplicación de datasets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class CreateDatasetInput:
    user_id: int
    name: str
    filename: str
    content: bytes
    description: str = ""


@dataclass(frozen=True)
class ProcessDatasetInput:
    dataset_id: int
    user_id: int


@dataclass(frozen=True)
class ListDatasetsInput:
    user_id: int


@dataclass(frozen=True)
class GetDatasetInput:
    user_id: int
    dataset_id: int


@dataclass(frozen=True)
class DeleteDatasetInput:
    user_id: int
    dataset_id: int


@dataclass(frozen=True)
class DatasetTableDTO:
    id: int | None
    table_name: str
    row_count: int
    column_count: int
    columns: list[dict[str, Any]]


@dataclass(frozen=True)
class DatasetDTO:
    id: int | None
    user_id: int
    name: str
    description: str
    file_size: int
    schema: dict[str, Any]
    row_count: int
    column_count: int
    status: str
    error_message: str
    created_at: datetime | None
    updated_at: datetime | None
    tables: tuple[DatasetTableDTO, ...] = ()
