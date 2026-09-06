# apps/queries/services/query_service.py
from .pipeline import DatasetGuard, CacheLayer, EngineRouter, Persistence, QuotaUpdater, ResponseBuilder


class QueryService:
    @staticmethod
    def execute(question: str, dataset_id: int, user) -> dict:
        pipeline = [DatasetGuard(), CacheLayer(), EngineRouter(), Persistence(), QuotaUpdater(), ResponseBuilder()]
        context = {'question': question, 'dataset_id': dataset_id, 'user': user}
        
        try:
            for m in pipeline:
                context = m.process(context)
                if isinstance(m, CacheLayer) and context.get('cached'):
                    return context['response']
            return context['response']
        finally:
            if 'got_lock' in context:
                CacheLayer().release_lock(context)
