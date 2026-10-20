"""Legacy package facade; ORM declarations live in infrastructure.models."""

from apps.queries.infrastructure.models import QueryFeedback, QueryHistory, QueryResult

__all__ = ["QueryFeedback", "QueryHistory", "QueryResult"]
