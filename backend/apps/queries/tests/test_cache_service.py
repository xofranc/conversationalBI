# apps/queries/tests/test_cache_service.py
import pytest

from apps.queries.services.cache_service import CacheService

PREGUNTA = 'ventas por mes'


class TestInvalidacionPorVersion:

    def test_misma_version_comparte_clave(self):
        CacheService.set(PREGUNTA, 1, {'data': [1]}, version='v1')
        assert CacheService.get(PREGUNTA, 1, 'v1') == {'data': [1]}

    def test_version_distinta_invalida_el_cache(self):
        CacheService.set(PREGUNTA, 1, {'data': [1]}, version='v1')
        # Dataset reprocesado → updated_at cambia → miss
        assert CacheService.get(PREGUNTA, 1, 'v2') is None


class TestLockAntiStampede:

    def test_lock_es_exclusivo(self):
        assert CacheService.acquire_lock(PREGUNTA, 1) is True
        assert CacheService.acquire_lock(PREGUNTA, 1) is False

    def test_release_permite_readquirir(self):
        CacheService.acquire_lock(PREGUNTA, 1)
        CacheService.release_lock(PREGUNTA, 1)
        assert CacheService.acquire_lock(PREGUNTA, 1) is True
