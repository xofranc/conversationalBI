# apps/queries/services/pipeline/tests/test_cache_layer.py
import pytest
from unittest.mock import Mock, patch, MagicMock

from ..cache_layer import CacheLayer


@pytest.mark.django_db
def test_cache_layer_hit():
    middleware = CacheLayer()
    cached_data = {'sql': 'SELECT * FROM table', 'data': []}
    
    with patch.object(middleware, '_handle_cache_hit') as mock_hit:
        mock_hit.return_value = {'cached': True, 'response': cached_data}
        
        with patch('apps.queries.services.pipeline.cache_layer.CacheService.get', return_value=cached_data):
            context = {
                'question': 'test',
                'dataset_id': 1,
                'version': '1.0',
                'user': Mock()
            }
            result = middleware.process(context)
            
            assert result['cached'] is True
            assert result['response'] == cached_data


@pytest.mark.django_db
def test_cache_layer_miss():
    middleware = CacheLayer()
    
    with patch('apps.queries.services.pipeline.cache_layer.CacheService.get', return_value=None):
        with patch('apps.queries.services.pipeline.cache_layer.CacheService.acquire_lock', return_value=True):
            context = {
                'question': 'test',
                'dataset_id': 1,
                'version': '1.0',
                'user': Mock()
            }
            result = middleware.process(context)
            
            assert result['cached'] is False
            assert result['got_lock'] is True


@pytest.mark.django_db
def test_cache_layer_release_lock():
    middleware = CacheLayer()
    context = {
        'got_lock': True,
        'lock_key': ('question', 1, '1.0')
    }
    
    with patch('apps.queries.services.pipeline.cache_layer.CacheService.release_lock') as mock_release:
        middleware.release_lock(context)
        mock_release.assert_called_once_with('question', 1, '1.0')
