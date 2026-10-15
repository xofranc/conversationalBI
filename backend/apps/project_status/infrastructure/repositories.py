"""Repositorios ORM para fases y módulos del producto."""

from __future__ import annotations

from apps.project_status.domain.entities import (
    ProjectModule as ModuleEntity,
    ProjectModuleStatus,
    ProjectPhase as PhaseEntity,
    ProjectPhaseStatus,
)
from apps.project_status.domain.repositories import ProjectModuleRepository, ProjectPhaseRepository

from .models import ProjectModule as ModuleModel
from .models import ProjectPhase as PhaseModel


def _phase_entity(model: PhaseModel) -> PhaseEntity:
    return PhaseEntity(
        id=model.pk,
        order=model.order,
        name=model.name,
        description=model.description,
        status=ProjectPhaseStatus(model.status),
        date_completed=model.date_completed,
        github_url=model.github_url,
        doc_url=model.doc_url,
    )


def _module_entity(model: ModuleModel) -> ModuleEntity:
    return ModuleEntity(
        id=model.pk,
        order=model.order,
        name=model.name,
        description=model.description,
        status=ProjectModuleStatus(model.status),
        icon=model.icon,
    )


class DjangoProjectPhaseRepository(ProjectPhaseRepository):
    def get_by_id(self, phase_id: int) -> PhaseEntity | None:
        model = PhaseModel.objects.filter(pk=phase_id).first()
        return _phase_entity(model) if model is not None else None

    def list_all(self) -> tuple[PhaseEntity, ...]:
        return tuple(_phase_entity(model) for model in PhaseModel.objects.all())

    def save(self, phase: PhaseEntity) -> PhaseEntity:
        values = {
            "order": phase.order,
            "name": phase.name,
            "description": phase.description,
            "status": phase.status.value,
            "date_completed": phase.date_completed,
            "github_url": phase.github_url,
            "doc_url": phase.doc_url,
        }
        if phase.id is None:
            model = PhaseModel.objects.create(**values)
        else:
            model, _ = PhaseModel.objects.update_or_create(pk=phase.id, defaults=values)
        return _phase_entity(model)

    def delete(self, phase_id: int) -> None:
        PhaseModel.objects.filter(pk=phase_id).delete()


class DjangoProjectModuleRepository(ProjectModuleRepository):
    def get_by_id(self, module_id: int) -> ModuleEntity | None:
        model = ModuleModel.objects.filter(pk=module_id).first()
        return _module_entity(model) if model is not None else None

    def list_all(self) -> tuple[ModuleEntity, ...]:
        return tuple(_module_entity(model) for model in ModuleModel.objects.all())

    def save(self, module: ModuleEntity) -> ModuleEntity:
        values = {
            "order": module.order,
            "name": module.name,
            "description": module.description,
            "status": module.status.value,
            "icon": module.icon,
        }
        if module.id is None:
            model = ModuleModel.objects.create(**values)
        else:
            model, _ = ModuleModel.objects.update_or_create(pk=module.id, defaults=values)
        return _module_entity(model)

    def delete(self, module_id: int) -> None:
        ModuleModel.objects.filter(pk=module_id).delete()
