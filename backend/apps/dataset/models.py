"""Legacy import facade; ORM declarations live in infrastructure.models."""

from apps.dataset.infrastructure.models import Dataset, DatasetTable

__all__ = ["Dataset", "DatasetTable"]
