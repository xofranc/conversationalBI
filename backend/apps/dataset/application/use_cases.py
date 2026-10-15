"""Casos de uso para crear, procesar y administrar datasets."""

from __future__ import annotations

from apps.dataset.domain.entities import Dataset, DatasetStatus, DatasetTable
from apps.dataset.domain.exceptions import DatasetFileTooLarge, UnsupportedDatasetFileExtension
from apps.dataset.domain.policies import DatasetUploadPolicy
from apps.dataset.domain.repositories import DatasetRepository, DatasetTableRepository

from .dtos import (
    CreateDatasetInput,
    DatasetDTO,
    DatasetTableDTO,
    DeleteDatasetInput,
    GetDatasetInput,
    ListDatasetsInput,
    ProcessDatasetInput,
)
from .ports import DatasetFileStorage, DatasetMaterializer, DatasetSchemaExtractor


class DatasetNotFound(LookupError):
    """El dataset solicitado no existe."""


class DatasetAccessDenied(PermissionError):
    """El usuario no es propietario del dataset."""


class DatasetUploadRejected(ValueError):
    """La policy de dominio rechazó el archivo que se intenta cargar."""


def _dataset_dto(dataset: Dataset, tables: tuple[DatasetTable, ...] = ()) -> DatasetDTO:
    return DatasetDTO(
        id=dataset.id,
        user_id=dataset.user_id,
        name=dataset.name,
        description=dataset.description,
        file_size=dataset.file_size,
        schema=dataset.schema_json,
        row_count=dataset.row_count,
        column_count=dataset.column_count,
        status=dataset.status.value,
        error_message=dataset.error_msg,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
        tables=tuple(
            DatasetTableDTO(
                id=table.id,
                table_name=table.table_name,
                row_count=table.row_count,
                column_count=table.column_count,
                columns=table.columns_json,
            )
            for table in tables
        ),
    )


class ProcessDataset:
    """Materializa un dataset, extrae schema/tablas y marca resultado final."""

    def __init__(
        self,
        datasets: DatasetRepository,
        tables: DatasetTableRepository,
        materializer: DatasetMaterializer,
        schema_extractor: DatasetSchemaExtractor,
    ) -> None:
        self._datasets = datasets
        self._tables = tables
        self._materializer = materializer
        self._schema_extractor = schema_extractor

    def execute(self, request: ProcessDatasetInput) -> DatasetDTO:
        dataset = self._datasets.get_by_id(request.dataset_id)
        if dataset is None:
            raise DatasetNotFound(f"Dataset {request.dataset_id} no encontrado")
        if dataset.user_id != request.user_id:
            raise DatasetAccessDenied("No tienes acceso a este dataset")

        try:
            materialized_path = self._materializer.materialize(dataset.id or request.dataset_id, dataset.file_path)
            dataset = self._datasets.save(Dataset(
                user_id=dataset.user_id,
                name=dataset.name,
                file_path=dataset.file_path,
                description=dataset.description,
                file_size=dataset.file_size,
                db_path=materialized_path,
                schema_json=dataset.schema_json,
                row_count=dataset.row_count,
                column_count=dataset.column_count,
                status=DatasetStatus.PROCESSING,
                error_msg=dataset.error_msg,
                created_at=dataset.created_at,
                updated_at=dataset.updated_at,
                id=dataset.id,
            ))

            schema = self._schema_extractor.extract(dataset.file_path)
            schema_tables = schema.get("tables", [])
            row_count = sum(int(table.get("row_count", 0)) for table in schema_tables)
            column_count = sum(len(table.get("columns", [])) for table in schema_tables)

            for table_data in schema_tables:
                table = DatasetTable(
                    dataset_id=dataset.id or request.dataset_id,
                    table_name=str(table_data["name"]),
                    row_count=int(table_data.get("row_count", 0)),
                    column_count=len(table_data.get("columns", [])),
                    columns_json=list(table_data.get("columns", [])),
                )
                self._tables.save(table)

            ready = dataset.mark_ready(schema, row_count, column_count)
            return _dataset_dto(self._datasets.save(ready), self._tables.list_by_dataset(request.dataset_id))
        except Exception as error:
            current = self._datasets.get_by_id(request.dataset_id) or dataset
            self._datasets.save(current.mark_error(str(error)))
            raise


class CreateDataset:
    """Crea el registro y procesa el archivo mediante ports independientes."""

    def __init__(
        self,
        datasets: DatasetRepository,
        file_storage: DatasetFileStorage,
        process_dataset: ProcessDataset,
    ) -> None:
        self._datasets = datasets
        self._file_storage = file_storage
        self._process_dataset = process_dataset

    def execute(self, request: CreateDatasetInput) -> DatasetDTO:
        size = len(request.content)
        try:
            DatasetUploadPolicy.validate(request.filename, size)
        except (UnsupportedDatasetFileExtension, DatasetFileTooLarge) as error:
            raise DatasetUploadRejected(str(error)) from error

        dataset = self._datasets.save(Dataset(
            user_id=request.user_id,
            name=request.name,
            file_path="",
            description=request.description,
            file_size=size,
            status=DatasetStatus.PROCESSING,
        ))
        try:
            stored_path = self._file_storage.store(request.filename, request.content, request.user_id)
            dataset = self._datasets.save(Dataset(
                user_id=dataset.user_id,
                name=dataset.name,
                file_path=stored_path,
                description=dataset.description,
                file_size=dataset.file_size,
                db_path=dataset.db_path,
                schema_json=dataset.schema_json,
                row_count=dataset.row_count,
                column_count=dataset.column_count,
                status=DatasetStatus.PROCESSING,
                error_msg=dataset.error_msg,
                created_at=dataset.created_at,
                updated_at=dataset.updated_at,
                id=dataset.id,
            ))
        except Exception as error:
            self._datasets.save(dataset.mark_error(str(error)))
            raise
        if dataset.id is None:
            raise RuntimeError("El repositorio debe asignar identidad al dataset creado")
        return self._process_dataset.execute(ProcessDatasetInput(
            dataset_id=dataset.id,
            user_id=request.user_id,
        ))


class ListDatasets:
    """Lista datasets del usuario autenticado o demo."""

    def __init__(self, datasets: DatasetRepository) -> None:
        self._datasets = datasets

    def execute(self, request: ListDatasetsInput) -> tuple[DatasetDTO, ...]:
        return tuple(_dataset_dto(dataset) for dataset in self._datasets.list_by_user(request.user_id))


class GetDataset:
    """Obtiene un dataset solo si pertenece al usuario."""

    def __init__(self, datasets: DatasetRepository, tables: DatasetTableRepository) -> None:
        self._datasets = datasets
        self._tables = tables

    def execute(self, request: GetDatasetInput) -> DatasetDTO:
        dataset = self._datasets.get_by_id(request.dataset_id)
        if dataset is None:
            raise DatasetNotFound(f"Dataset {request.dataset_id} no encontrado")
        if dataset.user_id != request.user_id:
            raise DatasetAccessDenied("No tienes acceso a este dataset")
        return _dataset_dto(dataset, self._tables.list_by_dataset(request.dataset_id))


class DeleteDataset:
    """Elimina primero el registro y después recursos externos asociados."""

    def __init__(
        self,
        datasets: DatasetRepository,
        file_storage: DatasetFileStorage,
        materializer: DatasetMaterializer,
    ) -> None:
        self._datasets = datasets
        self._file_storage = file_storage
        self._materializer = materializer

    def execute(self, request: DeleteDatasetInput) -> None:
        dataset = self._datasets.get_by_id(request.dataset_id)
        if dataset is None:
            raise DatasetNotFound(f"Dataset {request.dataset_id} no encontrado")
        if dataset.user_id != request.user_id:
            raise DatasetAccessDenied("No tienes permiso para eliminar este dataset")

        self._datasets.delete(request.dataset_id)
        self._file_storage.delete(dataset.file_path)
        self._materializer.delete(dataset.db_path)
