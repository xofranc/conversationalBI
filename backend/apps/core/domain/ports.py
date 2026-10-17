"""Contratos de dominio para coordinar el ciclo de vida demo."""

from __future__ import annotations

from typing import Protocol, Sequence

from .value_objects import DemoDatasetDTO


class DemoDatasetLifecycle(Protocol):
    """Permite enumerar y borrar datasets asociados a un usuario demo."""

    def list_for_user(self, user_id: int) -> Sequence[DemoDatasetDTO]: ...

    def list_ids_for_user(self, user_id: int) -> Sequence[int]: ...

    def delete(self, dataset_id: int, user_id: int) -> None: ...
