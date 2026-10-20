"""Contratos de persistencia para roadmap y módulos."""

from __future__ import annotations

from typing import Protocol, Sequence

from .entities import ProjectModule, ProjectPhase


class ProjectPhaseRepository(Protocol):
    def get_by_id(self, phase_id: int) -> ProjectPhase | None: ...

    def list_all(self) -> Sequence[ProjectPhase]: ...

    def save(self, phase: ProjectPhase) -> ProjectPhase: ...

    def delete(self, phase_id: int) -> None: ...


class ProjectModuleRepository(Protocol):
    def get_by_id(self, module_id: int) -> ProjectModule | None: ...

    def list_all(self) -> Sequence[ProjectModule]: ...

    def save(self, module: ProjectModule) -> ProjectModule: ...

    def delete(self, module_id: int) -> None: ...
