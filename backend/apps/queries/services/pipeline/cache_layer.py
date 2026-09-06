# apps/queries/services/pipeline/cache_layer.py
import time

from .base import Middleware
from ..cache_service import CacheService
from ..repositories import QueryRepository
from apps.users.services import UserService


class CacheLayer(Middleware):
    """Handles cache lookup, anti-stampede, and cache storage."""
    
    def process(self, context: dict) -> dict:
        question = context['question']
        dataset_id = context['dataset_id']
        version = context['version']
        user = context['user']
        
        # Check cache
        cached = CacheService.get(question, dataset_id, version)
        if cached:
            return self._handle_cache_hit(context, cached, question, dataset_id, user)
        
        # Anti-stampede: if another worker is computing, wait for cache
        got_lock = CacheService.acquire_lock(question, dataset_id, version)
        if not got_lock:
            for _ in range(5):
                time.sleep(1)
                cached = CacheService.get(question, dataset_id, version)
                if cached:
                    return self._handle_cache_hit(context, cached, question, dataset_id, user)
        
        # No cache hit, proceed with query
        context['cached'] = False
        context['got_lock'] = got_lock
        context['lock_key'] = (question, dataset_id, version)
        
        return context
    
    def _handle_cache_hit(self, context: dict, cached: dict, question: str, 
                          dataset_id: int, user) -> dict:
        """Handle cache hit by persisting and returning cached response."""
        # Persist cache hit to history
        query = QueryRepository.save_query(
            user=user,
            dataset_id=dataset_id,
            question=question,
            sql_generated=cached.get('sql', ''),
            execution_time=0.0,
            success=True,
            error_msg='',
            model_used=cached.get('model_used', ''),
            retry_count=0,
            cached=True,
        )
        
        # Update quota
        UserService.increment_usage(user)
        
        # Return cached response with new query_id
        context['cached'] = True
        context['response'] = {**cached, 'cached': True, 'query_id': query.id}
        return context
    
    def release_lock(self, context: dict) -> None:
        """Release the lock if we acquired it."""
        if context.get('got_lock'):
            question, dataset_id, version = context['lock_key']
            CacheService.release_lock(question, dataset_id, version)
