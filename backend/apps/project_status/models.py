"""Legacy import facade; ORM declarations live in infrastructure.models."""

from apps.project_status.infrastructure.models import ProjectModule, ProjectPhase

__all__ = ["ProjectModule", "ProjectPhase"]
