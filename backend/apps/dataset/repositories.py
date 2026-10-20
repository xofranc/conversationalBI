"""Internal compatibility facade for dataset persistence imports.

The legacy create/get helpers are not part of the entity-based repository API;
callers should use the concrete repositories' get_by_id/list_by_user/save methods.
"""

from apps.dataset.infrastructure.repositories import (
    DjangoDatasetRepository,
    DjangoDatasetTableRepository,
)

DatasetRepository = DjangoDatasetRepository
DatasetTableRepository = DjangoDatasetTableRepository

__all__ = [
    "DatasetRepository",
    "DatasetTableRepository",
    "DjangoDatasetRepository",
    "DjangoDatasetTableRepository",
]
