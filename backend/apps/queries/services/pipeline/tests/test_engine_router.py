# apps/queries/services/pipeline/tests/test_engine_router.py
import pytest
from unittest.mock import Mock, patch

from ..engine_router import EngineRouter


@pytest.mark.django_db
def test_engine_router_with_analysis():
    middleware = EngineRouter()
    
    with patch('apps.queries.services.pipeline.engine_router.detect_analysis', return_value='forecast'):
        with patch('apps.queries.services.pipeline.engine_router.AnalysisService.execute') as mock_analysis:
            mock_analysis.return_value = {'sql': 'SELECT *', 'data': []}
            
            context = {
                'question': 'forecast sales',
                'dataset_id': 1,
                'dataset': Mock(schema_json={}),
                'user': Mock()
            }
            result = middleware.process(context)
            
            assert 'engine_result' in result
            mock_analysis.assert_called_once()


@pytest.mark.django_db
def test_engine_router_with_llm():
    middleware = EngineRouter()
    
    with patch('apps.queries.services.pipeline.engine_router.detect_analysis', return_value=None):
        with patch('apps.queries.services.pipeline.engine_router.AIQueryService.execute') as mock_llm:
            mock_llm.return_value = {'sql': 'SELECT *', 'data': []}
            
            context = {
                'question': 'show sales',
                'dataset_id': 1,
                'dataset': Mock(schema_json={}),
                'user': Mock()
            }
            result = middleware.process(context)
            
            assert 'engine_result' in result
            mock_llm.assert_called_once()
