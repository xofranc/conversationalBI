# apps/queries/services/pipeline/response_builder.py
from .base import Middleware
from ..cache_service import CacheService


class ResponseBuilder(Middleware):
    """Builds final response and handles cache storage."""
    
    def process(self, context: dict) -> dict:
        query = context['query']
        result = context['result']
        cached = context['cached']
        engine_result = context['engine_result']
        question = context['question']
        dataset_id = context['dataset_id']
        version = context['version']
        
        # Build response
        response = self._build_response(query, result, cached)
        
        # Add suggestions if query failed
        if not engine_result['success']:
            response['suggestions'] = engine_result.get('suggestions', [])
        
        # Cache successful results
        if engine_result['success']:
            CacheService.set(question, dataset_id, response, version)
        
        context['response'] = response
        return context
    
    def _build_response(self, query, result, cached: bool) -> dict:
        return {
            'query_id': query.id,
            'sql': query.sql_generated,
            'success': query.success,
            'error_msg': query.error_msg,
            'execution_time': query.execution_time,
            'model_used': query.model_used,
            'retry_count': query.retry_count,
            'cached': cached,
            'data': result.result_json if result else [],
            'columns': result.columns if result else [],
            'chart_type': result.chart_type if result else 'table',
            'chart_config': result.chart_config if result else {},
            'row_count': result.row_count if result else 0,
            'answer': result.answer if result else '',
        }
