"""Adaptadores de cache, transacción y materialización para application.queries."""

from __future__ import annotations

import hashlib
import json
import time
from contextlib import AbstractContextManager
from uuid import uuid4

from django.conf import settings
from django.core.cache import cache
from django.db import transaction

from apps.dataset.infrastructure.adapters import PostgresDatasetMaterializer
from apps.queries.application.dtos import QueryCacheKeyDTO, QueryResponseDTO


def _cache_key(namespace: str, key: QueryCacheKeyDTO) -> str:
    encoded = json.dumps(
        [key.question, key.dataset_id, key.dataset_version],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"conversationalbi:query:{namespace}:{hashlib.sha256(encoded).hexdigest()}"


class DjangoQueryCache:
    def __init__(self, *, timeout: int | None = None, lock_timeout: int = 120) -> None:
        self._timeout = timeout if timeout is not None else getattr(settings, "QUERY_CACHE_TIMEOUT", 300)
        self._lock_timeout = lock_timeout
        self._lock_tokens: dict[str, str] = {}

    def get(self, key: QueryCacheKeyDTO) -> QueryResponseDTO | None:
        value = cache.get(_cache_key("value", key))
        return value if isinstance(value, QueryResponseDTO) else None

    def set(self, key: QueryCacheKeyDTO, value: QueryResponseDTO) -> None:
        cache.set(_cache_key("value", key), value, timeout=self._timeout)

    def acquire_lock(self, key: QueryCacheKeyDTO) -> bool:
        lock_key = _cache_key("lock", key)
        token = uuid4().hex
        acquired = cache.add(lock_key, token, timeout=self._lock_timeout)
        if acquired:
            self._lock_tokens[lock_key] = token
        return acquired

    def release_lock(self, key: QueryCacheKeyDTO) -> None:
        lock_key = _cache_key("lock", key)
        token = self._lock_tokens.pop(lock_key, None)
        if token is not None and cache.get(lock_key) == token:
            cache.delete(lock_key)


class DjangoQueryTransaction:
    def atomic(self) -> AbstractContextManager[None]:
        return transaction.atomic()


class ThreadWaiter:
    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)


class QueryDatasetMaterializer:
    def __init__(self, materializer: PostgresDatasetMaterializer | None = None) -> None:
        self._materializer = materializer or PostgresDatasetMaterializer()

    def ensure_available(self, dataset_id: int, file_path: str, materialized_path: str) -> str:
        return self._materializer.ensure_available(dataset_id, file_path, materialized_path)
