# apps/queries/services/pipeline/tests/test_response_builder.py
import pytest
from unittest.mock import Mock, patch

from ..response_builder import ResponseBuilder


@pytest.mark.django_db
def test_response_builder_successful():
    middleware = ResponseBuilder()
    
    query = Mock()
    query.id = 1
    query.sql_generated = 'SELECT * FROM table'
    query.success = True
    query.error_msg = ''
    query.execution_time = 0.1
    query.model_used = 'gpt-4'
    query.retry_count = 0
    
    result = Mock()
    result.result_json = [{'id': 1}]
    result.columns = ['id']
    result.chart_type = 'bar'
    result.chart_config = {}
    result.row_count = 1
    result.answer = 'Test answer'
    
    with patch('apps.queries.services.pipeline.response_builder.CacheService.set'):
        context = {
            'query': query,
            'result': result,
            'cached': False,
            'engine_result': {'success': True},
            'question': 'test',
            'dataset_id': 1,
            'version': '1.0'
        }
        result_dict = middleware.process(context)
        
        assert 'response' in result_dict
        response = result_dict['response']
        assert response['query_id'] == 1
        assert response['sql'] == 'SELECT * FROM table'
        assert response['success'] is True
        assert response['data'] == [{'id': 1}]
        assert response['chart_type'] == 'bar'


@pytest.mark.django_db
def test_response_builder_failed():
    middleware = ResponseBuilder()
    
    query = Mock()
    query.id = 1
    query.sql_generated = ''
    query.success = False
    query.error_msg = 'Query failed'
    query.execution_time = 0.0
    query.model_used = ''
    query.retry_count = 0
    
    with patch('apps.queries.services.pipeline.response_builder.CacheService.set'):
        context = {
            'query': query,
            'result': None,
            'cached': False,
            'engine_result': {'success': False, 'suggestions': ['Try rephrasing']},
            'question': 'test',
            'dataset_id': 1,
            'version': '1.0'
        }
        result_dict = middleware.process(context)
        
        assert 'response' in result_dict
        response = result_dict['response']
        assert response['success'] is False
        assert response['suggestions'] == ['Try rephrasing']
