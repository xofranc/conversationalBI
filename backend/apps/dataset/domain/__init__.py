"""Dominio de datasets y sus tablas, sin dependencias de almacenamiento."""

from .entities import Dataset, DatasetStatus, DatasetTable
from .exceptions import (
    DatasetFileTooLarge,
    DatasetNotQueryable,
    DatasetOwnershipViolation,
    DomainError,
    UnsupportedDatasetFileExtension,
)
from .policies import DatasetOwnershipPolicy, DatasetUploadPolicy
from .ports import (
    DatasetDataReader,
    DatasetFileStorage,
    DatasetMaterializer,
    DatasetResourceCleanup,
    DatasetSchemaExtractor,
)

__all__ = [
    "Dataset",
    "DatasetDataReader",
    "DatasetFileTooLarge",
    "DatasetFileStorage",
    "DatasetMaterializer",
    "DatasetNotQueryable",
    "DatasetOwnershipPolicy",
    "DatasetOwnershipViolation",
    "DatasetResourceCleanup",
    "DatasetSchemaExtractor",
    "DatasetStatus",
    "DatasetTable",
    "DatasetUploadPolicy",
    "DomainError",
    "UnsupportedDatasetFileExtension",
]
