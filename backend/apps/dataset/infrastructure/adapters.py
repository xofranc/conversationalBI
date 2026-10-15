"""Storage, schema y base de datos detrás de los ports de application."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

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
