# Fixtures
import pytest
from rest_framework.test import APIClient
import os
import django

# Configurar Django ANTES de cualquier import
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()


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
        username='testuser',
        email='test@example.com',
        password='testpass123'
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