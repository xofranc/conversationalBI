# Fixtures
# La configuración de Django la gestiona pytest-django vía pytest.ini
# (DJANGO_SETTINGS_MODULE = config.settings)
import pytest
from rest_framework.test import APIClient


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
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )

@pytest.fixture
def test_dataset(test_user):
    """Fixture que crea un dataset de prueba"""
    from apps.dataset.models import Dataset
    return Dataset.objects.create(
        user=test_user,  # Nota: se llama 'user' no 'owner'
        name='Test Dataset',
        file_path='/tmp/test.csv',
        status=Dataset.Status.READY
    )