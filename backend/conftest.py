# Fixtures
# La configuración de Django la gestiona pytest-django vía pytest.ini
# (DJANGO_SETTINGS_MODULE = config.settings)
#
# OJO: los tests nunca tocan la BD del .env (puede ser Supabase de
# producción). Ese guard vive en settings.py (bloque _TESTING), no aquí:
# pytest-django importa settings ANTES que este conftest.
import os

import psycopg2
import pytest
from django.conf import settings
from rest_framework.test import APIClient


def _postgres_up() -> bool:
    """True si el Postgres de datasets (Docker local o Supabase) responde."""
    dsn = getattr(settings, "DATABASE_URL", "")
    if not dsn:
        return False
    try:
        psycopg2.connect(dsn, connect_timeout=2).close()
        return True
    except Exception:
        return False


# Tests que ejercitan la capa de datasets sobre Postgres real se saltan
# cuando no hay servidor: el resto de la suite sigue verde sin Docker.
requires_postgres = pytest.mark.skipif(
    not _postgres_up(),
    reason="Postgres no disponible (DATABASE_URL sin configurar o servidor apagado)",
)


@pytest.fixture
def materialized_dataset(db):
    """Materializa el archivo del dataset en su schema ds_<id> (Postgres)
    y elimina el schema al terminar el test."""
    from apps.dataset.services import DatabaseService

    schemas = []

    def _materialize(dataset):
        abs_file = os.path.join(settings.MEDIA_ROOT, dataset.file_path)
        dataset.db_path = DatabaseService.materialize(dataset.id, abs_file)
        dataset.save(update_fields=["db_path", "updated_at"])
        schemas.append(dataset.db_path)
        return dataset

    yield _materialize

    for schema in schemas:
        DatabaseService.delete(schema)


@pytest.fixture
def schema_cleanup():
    """Lista colectora: los tests anexan schemas ds_* y se eliminan al final."""
    from apps.dataset.services import DatabaseService

    schemas = []
    yield schemas
    for schema in schemas:
        DatabaseService.delete(schema)


@pytest.fixture(autouse=True)
def _clear_cache():
    """LocMemCache es global al proceso y sobrevive entre tests (la BD no).
    Sin esto, un CacheService.set() en un test contamina los siguientes."""
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    """Fixture que retorna un cliente API autenticado"""
    return APIClient()


@pytest.fixture
def test_user():
    """Fixture que crea un usuario de prueba"""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    return User.objects.create_user(
        email="test@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def test_dataset(test_user):
    """Fixture que crea un dataset de prueba"""
    from apps.dataset.models import Dataset

    return Dataset.objects.create(
        user=test_user,  # Nota: se llama 'user' no 'owner'
        name="Test Dataset",
        file_path="/tmp/test.csv",
        status=Dataset.Status.READY,
    )
