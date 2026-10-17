"""Repositorios ORM que traducen entidades de dataset a modelos Django."""

from __future__ import annotations

from django.db import transaction

from apps.dataset.domain.entities import Dataset as DatasetEntity
from apps.dataset.domain.entities import DatasetStatus, DatasetTable as DatasetTableEntity
from apps.dataset.domain.policies import DatasetOwnershipPolicy
from apps.dataset.domain.repositories import DatasetRepository, DatasetTableRepository

from .models import Dataset as DatasetModel
from .models import DatasetTable as DatasetTableModel


def _dataset_entity(model: DatasetModel) -> DatasetEntity:
    return DatasetEntity(
        id=model.pk,
        user_id=model.user_id,
        name=model.name,
        description=model.description,
        file_path=model.file_path,
        file_size=model.file_size,
        db_path=model.db_path,
        schema_json=model.schema_json,
        row_count=model.row_count,
        column_count=model.column_count,
        status=DatasetStatus(model.status),
        error_msg=model.error_msg,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _table_entity(model: DatasetTableModel) -> DatasetTableEntity:
    return DatasetTableEntity(
        id=model.pk,
        dataset_id=model.dataset_id,
        table_name=model.table_name,
        row_count=model.row_count,
        column_count=model.column_count,
        columns_json=model.columns_json,
    )


class DjangoDatasetRepository(DatasetRepository):
    def get_by_id(self, dataset_id: int) -> DatasetEntity | None:
        model = DatasetModel.objects.filter(pk=dataset_id).first()
        return _dataset_entity(model) if model is not None else None

    def list_by_user(self, user_id: int) -> tuple[DatasetEntity, ...]:
        return tuple(_dataset_entity(model) for model in DatasetModel.objects.filter(user_id=user_id))

    def save(self, dataset: DatasetEntity) -> DatasetEntity:
        values = {
            "user_id": dataset.user_id,
            "name": dataset.name,
            "description": dataset.description,
            "file_path": dataset.file_path,
            "file_size": dataset.file_size,
            "db_path": dataset.db_path,
            "schema_json": dataset.schema_json,
            "row_count": dataset.row_count,
            "column_count": dataset.column_count,
            "status": dataset.status.value,
            "error_msg": dataset.error_msg,
        }
        if dataset.id is None:
            model = DatasetModel.objects.create(**values)
        else:
            model, _ = DatasetModel.objects.update_or_create(pk=dataset.id, defaults=values)
        return _dataset_entity(model)

    def delete(self, dataset_id: int) -> None:
        DatasetModel.objects.filter(pk=dataset_id).delete()

    def delete_for_owner(self, dataset_id: int, user_id: int) -> bool:
        with transaction.atomic():
            model = DatasetModel.objects.select_for_update().filter(pk=dataset_id).first()
            if model is None:
                return False

            dataset = _dataset_entity(model)
            if not DatasetOwnershipPolicy.owns(dataset, user_id):
                return False

            model.delete()
            return True


class DjangoDatasetTableRepository(DatasetTableRepository):
    def get_by_id(self, table_id: int) -> DatasetTableEntity | None:
        model = DatasetTableModel.objects.filter(pk=table_id).first()
        return _table_entity(model) if model is not None else None

    def get_by_name(self, dataset_id: int, table_name: str) -> DatasetTableEntity | None:
        model = DatasetTableModel.objects.filter(
            dataset_id=dataset_id, table_name=table_name
        ).first()
        return _table_entity(model) if model is not None else None

    def list_by_dataset(self, dataset_id: int) -> tuple[DatasetTableEntity, ...]:
        return tuple(
            _table_entity(model)
            for model in DatasetTableModel.objects.filter(dataset_id=dataset_id)
        )

    def save(self, table: DatasetTableEntity) -> DatasetTableEntity:
        values = {
            "dataset_id": table.dataset_id,
            "table_name": table.table_name,
            "row_count": table.row_count,
            "column_count": table.column_count,
            "columns_json": table.columns_json,
        }
        if table.id is not None:
            model, _ = DatasetTableModel.objects.update_or_create(pk=table.id, defaults=values)
        else:
            model, _ = DatasetTableModel.objects.update_or_create(
                dataset_id=table.dataset_id,
                table_name=table.table_name,
                defaults=values,
            )
        return _table_entity(model)

    def delete_for_dataset(self, dataset_id: int) -> None:
        DatasetTableModel.objects.filter(dataset_id=dataset_id).delete()
