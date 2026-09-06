# apps/queries/services/pipeline/tests/test_persistence.py
import pytest
from unittest.mock import Mock, patch

from ..persistence import Persistence


@pytest.mark.django_db
def test_persistence_successful_query():
    middleware = Persistence()
    
    with patch('apps.queries.services.pipeline.persistence.QueryRepository.save_query') as mock_save_query:
        with patch('apps.queries.services.pipeline.persistence.QueryRepository.save_result') as mock_save_result:
            mock_query = Mock()
            mock_save_query.return_value = mock_query
            
            context = {
                'engine_result': {
                    'sql': 'SELECT * FROM table',
                    'execution_time': 0.1,
                    'success': True,
                    'error_msg': '',
                    'retry_count': 0,
                    'rows': [{'id': 1}],
                    'columns': ['id'],
                    'chart_type': 'bar',
                    'chart_config': {},
                    'answer': 'Test answer'
                },
                'user': Mock(),
                'dataset_id': 1,
                'question': 'test question',
                'cached': False
            }
            result = middleware.process(context)
            
            assert result['query'] == mock_query
            assert result['result'] is not None
            mock_save_query.assert_called_once()
            mock_save_result.assert_called_once()


@pytest.mark.django_db
def test_persistence_failed_query():
    middleware = Persistence()
    
    with patch('apps.queries.services.pipeline.persistence.QueryRepository.save_query') as mock_save_query:
        mock_query = Mock()
        mock_save_query.return_value = mock_query
        
        context = {
            'engine_result': {
                'sql': '',
                'execution_time': 0.0,
                'success': False,
                'error_msg': 'Query failed',
                'retry_count': 0,
                'rows': [],
                'columns': [],
                'chart_type': 'table',
                'chart_config': {},
                'answer': ''
            },
            'user': Mock(),
            'dataset_id': 1,
            'question': 'test question',
            'cached': False
        }
        result = middleware.process(context)
        
        assert result['query'] == mock_query
        assert result['result'] is None
