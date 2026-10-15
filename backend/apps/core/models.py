"""Legacy import facade; ORM declarations live in infrastructure.models."""

from apps.core.infrastructure.models import DemoSession

__all__ = ["DemoSession"]
