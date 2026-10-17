"""DTOs de salida para fases y módulos del proyecto."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ProjectPhaseDTO:
    id: int | None
    order: int
    name: str
    description: str
    status: str
    date_completed: date | None
    github_url: str
    doc_url: str


@dataclass(frozen=True)
class ProjectModuleDTO:
    id: int | None
    order: int
    name: str
    description: str
    status: str
    icon: str


@dataclass(frozen=True)
class ProjectStatusDTO:
    phases: tuple[ProjectPhaseDTO, ...]
    modules: tuple[ProjectModuleDTO, ...]
