"""Storage, schema y base de datos detrás de los ports de application."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from apps.dataset.domain.exceptions import DatasetOwnershipViolation
from apps.dataset.domain.policies import DatasetOwnershipPolicy
from apps.dataset.domain.ports import (
    DatasetFileStorage,
    DatasetMaterializer,
    DatasetResourceCleanup,
)
from apps.dataset.domain.repositories import DatasetRepository

from .database_service import DatabaseService
from .schema_service import SchemaService


def _media_path(relative_path: str) -> str:
    root = Path(settings.MEDIA_ROOT).resolve()
    path = (root / relative_path).resolve()
    if path != root and root not in path.parents:
        raise ValueError("La ruta del dataset está fuera de MEDIA_ROOT")
    return str(path)


class DjangoDatasetFileStorage:
    def store(self, filename: str, content: bytes, user_id: int) -> str:
        extension = os.path.splitext(filename)[1].lower()
        relative_name = f"datasets/{user_id}/{uuid4().hex}{extension}"
        return default_storage.save(relative_name, ContentFile(content))

    def delete(self, file_path: str) -> None:
        if file_path:
            _media_path(file_path)
            default_storage.delete(file_path)


class DjangoDatasetSchemaExtractor:
    def extract(self, file_path: str) -> dict:
        return SchemaService.extract(_media_path(file_path))


class PostgresDatasetMaterializer:
    """Materializa el archivo y gestiona el schema de base de datos del dataset."""

    def materialize(self, dataset_id: int, file_path: str) -> str:
        return DatabaseService.materialize(dataset_id, _media_path(file_path))

    def delete(self, materialized_path: str) -> None:
        DatabaseService.delete(materialized_path)

    def ensure_available(
        self, dataset_id: int, file_path: str, materialized_path: str
    ) -> str:
        if materialized_path and DatabaseService.exists(materialized_path):
            return materialized_path
        return self.materialize(dataset_id, file_path)


class DjangoDatasetResourceCleanup(DatasetResourceCleanup):
    """Elimina el registro y sus recursos externos en orden determinista."""

    def __init__(
        self,
        datasets: DatasetRepository,
        file_storage: DatasetFileStorage,
        materializer: DatasetMaterializer,
    ) -> None:
        self._datasets = datasets
        self._file_storage = file_storage
        self._materializer = materializer

    def delete(self, dataset_id: int, user_id: int) -> None:
        dataset = self._datasets.get_by_id(dataset_id)
        if dataset is None:
            return
        if not DatasetOwnershipPolicy.owns(dataset, user_id):
            raise DatasetOwnershipViolation(
                "No tienes permiso para eliminar este dataset"
            )

        if not self._datasets.delete_for_owner(dataset_id, user_id):
            current_dataset = self._datasets.get_by_id(dataset_id)
            if current_dataset is None:
                return
            if not DatasetOwnershipPolicy.owns(current_dataset, user_id):
                raise DatasetOwnershipViolation(
                    "No tienes permiso para eliminar este dataset"
                )
            return

        self._file_storage.delete(dataset.file_path)
        self._materializer.delete(dataset.db_path)
