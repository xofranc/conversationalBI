# apps/queries/services/cache_service.py
import hashlib
from django.core.cache import cache


class CacheService:
    TTL = 60 * 60      # 1 hora
    LOCK_TTL = 60      # segundos — lock anti-stampede

    @staticmethod
    def _key(question: str, dataset_id: int, version: str = '') -> str:
        # La versión (updated_at del dataset) invalida el caché
        # automáticamente cuando el dataset se reprocesa
        payload = f"{dataset_id}:{version}:{question.strip().lower()}"
        return f"query:{hashlib.sha256(payload.encode()).hexdigest()}"

    @classmethod
    def get(cls, question: str, dataset_id: int, version: str = ''):
        return cache.get(cls._key(question, dataset_id, version))

    @classmethod
    def set(cls, question: str, dataset_id: int, result: dict, version: str = '') -> None:
        cache.set(cls._key(question, dataset_id, version), result, timeout=cls.TTL)

    @classmethod
    def acquire_lock(cls, question: str, dataset_id: int, version: str = '') -> bool:
        """Lock anti-stampede: solo el primer worker calcula; los demás esperan."""
        return cache.add(f"lock:{cls._key(question, dataset_id, version)}", True, timeout=cls.LOCK_TTL)

    @classmethod
    def release_lock(cls, question: str, dataset_id: int, version: str = '') -> None:
        cache.delete(f"lock:{cls._key(question, dataset_id, version)}")
