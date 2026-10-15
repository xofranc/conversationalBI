"""Contratos de persistencia para datasets y tablas."""

from __future__ import annotations

from typing import Protocol, Sequence

from .entities import Dataset, DatasetTable


class DatasetRepository(Protocol):
    def get_by_id(self, dataset_id: int) -> Dataset | None: ...

    def list_by_user(self, user_id: int) -> Sequence[Dataset]: ...

    def save(self, dataset: Dataset) -> Dataset: ...

    def delete(self, dataset_id: int) -> None: ...


class DatasetTableRepository(Protocol):
    """La persistencia garantiza unicidad de table_name por dataset."""

    def get_by_id(self, table_id: int) -> DatasetTable | None: ...

    def get_by_name(self, dataset_id: int, table_name: str) -> DatasetTable | None: ...

    def list_by_dataset(self, dataset_id: int) -> Sequence[DatasetTable]: ...

    def save(self, table: DatasetTable) -> DatasetTable: ...

    def delete_for_dataset(self, dataset_id: int) -> None: ...
