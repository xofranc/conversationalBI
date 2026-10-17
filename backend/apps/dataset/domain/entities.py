"""Entidades inmutables de datasets y tablas persistidas."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum
from typing import Any

from .exceptions import DatasetNotQueryable


class DatasetStatus(str, Enum):
    READY = "ready"
    INACTIVE = "inactive"
    ERROR = "error"
    PROCESSING = "processing"
    UPLOADED = "uploaded"


@dataclass(frozen=True)
class Dataset:
    user_id: int
    name: str
    file_path: str
    description: str = ""
    file_size: int = 0
    db_path: str = ""
    schema_json: dict[str, Any] = field(default_factory=dict)
    row_count: int = 0
    column_count: int = 0
    status: DatasetStatus = DatasetStatus.PROCESSING
    error_msg: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
    id: int | None = None

    def mark_ready(self, schema: dict[str, Any], row_count: int, column_count: int = 0) -> "Dataset":
        """Refleja la transición existente; no restringe el estado de origen ni limpia error_msg."""
        return replace(
            self,
            schema_json=schema,
            row_count=row_count,
            column_count=column_count,
            status=DatasetStatus.READY,
        )

    def mark_error(self, message: str) -> "Dataset":
        """Refleja mark_error del modelo legado sin alterar metadatos procesados."""
        return replace(self, status=DatasetStatus.ERROR, error_msg=message)

    @property
    def is_queryable(self) -> bool:
        return self.status is DatasetStatus.READY

    def ensure_queryable(self) -> None:
        if not self.is_queryable:
            raise DatasetNotQueryable(f"Dataset {self.id!r} no está listo para consultar")


@dataclass(frozen=True)
class DatasetTable:
    """Tabla asociada a un dataset; (dataset_id, table_name) es clave única."""

    dataset_id: int
    table_name: str
    row_count: int = 0
    column_count: int = 0
    columns_json: list[dict[str, Any]] = field(default_factory=list)
    id: int | None = None
