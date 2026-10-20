"""Casos de uso de lectura del roadmap y módulos."""

from __future__ import annotations

from apps.project_status.domain.repositories import ProjectModuleRepository, ProjectPhaseRepository

from .dtos import ProjectModuleDTO, ProjectPhaseDTO, ProjectStatusDTO


class ListProjectPhases:
    """Devuelve las fases persistidas del proyecto."""

    def __init__(self, phases: ProjectPhaseRepository) -> None:
        self._phases = phases

    def execute(self) -> tuple[ProjectPhaseDTO, ...]:
        return tuple(
            ProjectPhaseDTO(
                id=phase.id,
                order=phase.order,
                name=phase.name,
                description=phase.description,
                status=phase.status.value,
                date_completed=phase.date_completed,
                github_url=phase.github_url,
                doc_url=phase.doc_url,
            )
            for phase in self._phases.list_all()
        )


class ListProjectModules:
    """Devuelve los módulos/capacidades persistidos del proyecto."""

    def __init__(self, modules: ProjectModuleRepository) -> None:
        self._modules = modules

    def execute(self) -> tuple[ProjectModuleDTO, ...]:
        return tuple(
            ProjectModuleDTO(
                id=module.id,
                order=module.order,
                name=module.name,
                description=module.description,
                status=module.status.value,
                icon=module.icon,
            )
            for module in self._modules.list_all()
        )


class GetProjectStatus:
    """Compone la lectura de roadmap y módulos en un único resultado de consulta."""

    def __init__(self, phases: ListProjectPhases, modules: ListProjectModules) -> None:
        self._phases = phases
        self._modules = modules

    def execute(self) -> ProjectStatusDTO:
        return ProjectStatusDTO(phases=self._phases.execute(), modules=self._modules.execute())
