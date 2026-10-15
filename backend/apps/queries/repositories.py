"""Internal compatibility facade for query persistence imports.

The former save_query/save_result helpers accepted Django models and built
chart configuration inline. The entity-based repositories expose save(entity)
instead; query history and result persistence now have separate repositories.
"""

from apps.queries.infrastructure.repositories import (
    DjangoQueryFeedbackRepository,
    DjangoQueryHistoryRepository,
    DjangoQueryResultRepository,
)

QueryRepository = DjangoQueryHistoryRepository

__all__ = [
    "QueryRepository",
    "DjangoQueryHistoryRepository",
    "DjangoQueryResultRepository",
    "DjangoQueryFeedbackRepository",
]
