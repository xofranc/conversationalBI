"""Implementaciones de reloj y ciclo de vida de datasets demo."""

from __future__ import annotations

from datetime import datetime

from django.utils import timezone

from apps.core.domain.ports import DemoDatasetLifecycle
from apps.core.domain.value_objects import DemoDatasetDTO
from apps.dataset.domain.ports import DatasetResourceCleanup
from apps.dataset.domain.repositories import DatasetRepository


class DjangoClock:
    def now(self) -> datetime:
        return timezone.now()


class DjangoDemoDatasetLifecycle(DemoDatasetLifecycle):
    def __init__(
        self,
        datasets: DatasetRepository,
        resource_cleanup: DatasetResourceCleanup,
    ) -> None:
        self._datasets = datasets
        self._resource_cleanup = resource_cleanup

    def list_for_user(self, user_id: int) -> tuple[DemoDatasetDTO, ...]:
        return tuple(
            DemoDatasetDTO(dataset_id=dataset.id, name=dataset.name, status=dataset.status.value)
            for dataset in self._datasets.list_by_user(user_id)
            if dataset.id is not None
        )

    def list_ids_for_user(self, user_id: int) -> tuple[int, ...]:
        return tuple(
            dataset.id
            for dataset in self._datasets.list_by_user(user_id)
            if dataset.id is not None
        )

    def delete(self, dataset_id: int, user_id: int) -> None:
        self._resource_cleanup.delete(dataset_id, user_id)
