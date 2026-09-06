# apps/queries/services/pipeline/persistence.py
from django.conf import settings
from django.db import transaction

from .base import Middleware
from ..repositories import QueryRepository


class Persistence(Middleware):
    """Saves query and result to database atomically."""
    
    def process(self, context: dict) -> dict:
        engine_result = context['engine_result']
        user = context['user']
        dataset_id = context['dataset_id']
        question = context['question']
        cached = context['cached']
        
        with transaction.atomic():
            query = QueryRepository.save_query(
                user=user,
                dataset_id=dataset_id,
                question=question,
                sql_generated=engine_result['sql'],
                execution_time=engine_result['execution_time'],
                success=engine_result['success'],
                error_msg=engine_result['error_msg'],
                model_used=engine_result.get('model_used') or getattr(settings, 'LLM_SQL_MODEL', ''),
                retry_count=engine_result['retry_count'],
                cached=cached,
            )
            
            result = None
            if engine_result['success']:
                result = QueryRepository.save_result(
                    query=query,
                    rows=engine_result['rows'],
                    columns=engine_result['columns'],
                    chart_type=engine_result['chart_type'],
                    chart_config=engine_result.get('chart_config'),
                    answer=engine_result.get('answer', ''),
                )
        
        context['query'] = query
        context['result'] = result
        return context
