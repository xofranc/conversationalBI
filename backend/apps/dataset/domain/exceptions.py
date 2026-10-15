"""Excepciones propias del dominio de datasets."""


class DomainError(Exception):
    """Base para errores de negocio de esta app."""


class DatasetNotQueryable(DomainError):
    """El dataset no está en el estado READY requerido por las consultas."""


class UnsupportedDatasetFileExtension(DomainError):
    """La extensión del archivo no está soportada para una carga de dataset."""

    def __init__(self, filename: str) -> None:
        self.filename = filename
        super().__init__(f"Extensión de archivo no soportada: {filename!r}")


class DatasetFileTooLarge(DomainError):
    """El archivo supera el tamaño máximo permitido para una carga."""

    def __init__(self, size_bytes: int, max_size_bytes: int) -> None:
        self.size_bytes = size_bytes
        self.max_size_bytes = max_size_bytes
        super().__init__(
            f"El archivo tiene {size_bytes} bytes; el máximo permitido es {max_size_bytes} bytes."
        )
