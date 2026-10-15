"""Composition root de los casos de uso de dataset."""

from apps.dataset.application.use_cases import (
    CreateDataset,
    DeleteDataset,
    GetDataset,
    ListDatasets,
    ProcessDataset,
)

from .adapters import DjangoDatasetFileStorage, DjangoDatasetSchemaExtractor, PostgresDatasetMaterializer
from .repositories import DjangoDatasetRepository, DjangoDatasetTableRepository


def build_dataset_use_cases() -> dict[str, object]:
    datasets = DjangoDatasetRepository()
    tables = DjangoDatasetTableRepository()
    files = DjangoDatasetFileStorage()
    materializer = PostgresDatasetMaterializer()
    process = ProcessDataset(datasets, tables, materializer, DjangoDatasetSchemaExtractor())
    return {
        "create": CreateDataset(datasets, files, process),
        "process": process,
        "list": ListDatasets(datasets),
        "get": GetDataset(datasets, tables),
        "delete": DeleteDataset(datasets, files, materializer),
        "datasets": datasets,
        "tables": tables,
    }
