"""Policies puras de negocio para cargas de archivos de datasets."""

from .entities import Dataset
from .exceptions import (
    DatasetFileTooLarge,
    DatasetOwnershipViolation,
    UnsupportedDatasetFileExtension,
)


class DatasetOwnershipPolicy:
    """Regla canónica para comprobar la propiedad de un dataset."""

    @staticmethod
    def owns(dataset: Dataset, user_id: int) -> bool:
        """Indica si el usuario es propietario del dataset."""
        return dataset.user_id == user_id

    @staticmethod
    def assert_owner(dataset: Dataset, user_id: int) -> None:
        """Wrapper compatible que lanza un error si el usuario no es propietario."""
        if not DatasetOwnershipPolicy.owns(dataset, user_id):
            raise DatasetOwnershipViolation()


class DatasetUploadPolicy:
    """Valida formato y tamaño de un archivo antes de su carga."""

    ALLOWED_EXTENSIONS = frozenset({".csv", ".xlsx", ".json"})
    MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024

    @classmethod
    def validate(cls, filename: str, size_bytes: int) -> None:
        """Acepta extensiones válidas sin distinguir mayúsculas y hasta 50 MiB inclusivos."""
        extension = filename[filename.rfind(".") :].lower()
        if extension not in cls.ALLOWED_EXTENSIONS:
            raise UnsupportedDatasetFileExtension(filename)

        if size_bytes > cls.MAX_FILE_SIZE_BYTES:
            raise DatasetFileTooLarge(size_bytes, cls.MAX_FILE_SIZE_BYTES)
