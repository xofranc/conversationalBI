# apps/queries/services/pipeline/tests/test_dataset_guard.py
import pytest
from unittest.mock import Mock, patch
from rest_framework.exceptions import NotFound, ValidationError

from ..dataset_guard import DatasetGuard


@pytest.mark.django_db
def test_dataset_guard_valid_dataset():
    middleware = DatasetGuard()
    dataset = Mock()
    dataset.status = 'READY'
    dataset.updated_at.isoformat.return_value = '2024-01-01T00:00:00'
    
    with patch('apps.dataset.repositories.DatasetRepository.get_by_id', return_value=dataset):
        with patch('apps.dataset.services.database_service.DatabaseService.exists', return_value=True):
            context = {'dataset_id': 1}
            result = middleware.process(context)
            
            assert result['dataset'] == dataset
            assert result['version'] == '2024-01-01T00:00:00'


@pytest.mark.django_db
def test_dataset_guard_not_found():
    middleware = DatasetGuard()
    
    with patch('apps.dataset.repositories.DatasetRepository.get_by_id', side_effect=Exception('Not found')):
        context = {'dataset_id': 999}
        with pytest.raises(Exception):
            middleware.process(context)


@pytest.mark.django_db
def test_dataset_guard_not_ready():
    middleware = DatasetGuard()
    dataset = Mock()
    dataset.status = 'PROCESSING'
    
    with patch('apps.dataset.repositories.DatasetRepository.get_by_id', return_value=dataset):
        context = {'dataset_id': 1}
        with pytest.raises(ValidationError):
            middleware.process(context)
