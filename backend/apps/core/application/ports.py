"""Puertos para reloj y coordinación con el ciclo de vida de datasets demo."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, Sequence

from .dtos import DemoDatasetDTO


class Clock(Protocol):
    def now(self) -> datetime: ...


class DemoDatasetLifecycle(Protocol):
    def list_for_user(self, user_id: int) -> Sequence[DemoDatasetDTO]: ...

    def list_ids_for_user(self, user_id: int) -> Sequence[int]: ...

    def delete(self, dataset_id: int, user_id: int) -> None: ...
