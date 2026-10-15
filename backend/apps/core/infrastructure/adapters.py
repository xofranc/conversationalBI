"""Implementaciones de reloj y ciclo de vida de datasets demo."""

from __future__ import annotations

from datetime import datetime

from django.utils import timezone

from apps.core.application.dtos import DemoDatasetDTO
from apps.dataset.application.dtos import DeleteDatasetInput
from apps.dataset.application.use_cases import DeleteDataset
from apps.dataset.infrastructure.models import Dataset


class DjangoClock:
    def now(self) -> datetime:
        return timezone.now()


class DjangoDemoDatasetLifecycle:
    def __init__(self, delete_dataset: DeleteDataset) -> None:
        self._delete_dataset = delete_dataset

    def list_for_user(self, user_id: int) -> tuple[DemoDatasetDTO, ...]:
        return tuple(
            DemoDatasetDTO(dataset_id=model.pk, name=model.name, status=model.status)
            for model in Dataset.objects.filter(user_id=user_id)
        )

    def list_ids_for_user(self, user_id: int) -> tuple[int, ...]:
        return tuple(Dataset.objects.filter(user_id=user_id).values_list("pk", flat=True))

    def delete(self, dataset_id: int, user_id: int) -> None:
        self._delete_dataset.execute(DeleteDatasetInput(user_id=user_id, dataset_id=dataset_id))
