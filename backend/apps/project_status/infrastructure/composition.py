"""Composition root para lecturas del estado del proyecto."""

from apps.project_status.application.use_cases import (
    GetProjectStatus,
    ListProjectModules,
    ListProjectPhases,
)

from .repositories import DjangoProjectModuleRepository, DjangoProjectPhaseRepository


def build_project_status_use_cases() -> dict[str, object]:
    phases = ListProjectPhases(DjangoProjectPhaseRepository())
    modules = ListProjectModules(DjangoProjectModuleRepository())
    return {
        "list_phases": phases,
        "list_modules": modules,
        "get_status": GetProjectStatus(phases, modules),
    }
