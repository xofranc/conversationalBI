"""Entidades de roadmap y capacidades del producto."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class ProjectPhaseStatus(str, Enum):
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    BLOCKED = "blocked"


class ProjectModuleStatus(str, Enum):
    LIVE = "live"
    BETA = "beta"
    ALPHA = "alpha"
    PENDING = "pending"


@dataclass(frozen=True)
class ProjectPhase:
    order: int
    name: str
    description: str = ""
    status: ProjectPhaseStatus = ProjectPhaseStatus.PENDING
    date_completed: date | None = None
    github_url: str = ""
    doc_url: str = ""
    id: int | None = None


@dataclass(frozen=True)
class ProjectModule:
    order: int
    name: str
    description: str = ""
    status: ProjectModuleStatus = ProjectModuleStatus.PENDING
    icon: str = ""
    id: int | None = None
