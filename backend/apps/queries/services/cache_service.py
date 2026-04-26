# apps/queries/services/cache_service.py
import hashlib
import json
from django.core.cache import cache


class CacheService:
    TTL = 60 * 60   # 1 hora

    @staticmethod
    def _key(question: str, dataset_id: int) -> str:
        payload = f"{dataset_id}:{question.strip().lower()}"
        return f"query:{hashlib.md5(payload.encode()).hexdigest()}"

    @classmethod
    def get(cls, question: str, dataset_id: int):
        return cache.get(cls._key(question, dataset_id))

    @classmethod
    def set(cls, question: str, dataset_id: int, result: dict) -> None:
        cache.set(cls._key(question, dataset_id), result, timeout=cls.TTL)