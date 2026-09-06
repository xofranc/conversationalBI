# apps/queries/services/pipeline/engine_router.py
import logging
from .base import Middleware
from services.ai import AIQueryService
from services.analysis import AnalysisService, detect as detect_analysis
from apps.queries.repositories import QueryRepository

logger = logging.getLogger(__name__)

# How many previous queries to include as conversation context
HISTORY_CONTEXT = 3


class EngineRouter(Middleware):
    """Routes query to appropriate engine (statistical analysis or LLM)."""
    
    def process(self, context: dict) -> dict:
        question = context['question']
        dataset_id = context['dataset_id']
        dataset = context['dataset']
        user = context['user']
        
        logger.info('[EngineRouter] question="%s", dataset_id=%s', question, dataset_id)
        
        # Detect if statistical analysis is needed
        analysis_type = detect_analysis(question)
        logger.info('[EngineRouter] analysis_type=%s', analysis_type)
        
        if analysis_type:
            # Statistical analysis engine
            logger.info('[EngineRouter] Usando AnalysisService...')
            engine_result = AnalysisService.execute(
                analysis_type=analysis_type,
                dataset_id=dataset_id,
                question=question,
            )
        else:
            # LLM engine with conversation context
            history = self._conversation_context(user, dataset_id)
            logger.info('[EngineRouter] Usando AIQueryService, history_items=%s', len(history))
            engine_result = AIQueryService.execute(
                question=question,
                dataset_id=dataset_id,
                schema=dataset.schema_json,
                history=history,
            )
        
        logger.info('[EngineRouter] engine_result: success=%s, sql=%s', engine_result.get('success'), engine_result.get('sql', '')[:100])
        context['engine_result'] = engine_result
        return context
    
    def _conversation_context(self, user, dataset_id: int) -> list:
        """Get recent successful queries for conversation context."""
        from apps.queries.models import QueryHistory
        
        recientes = (
            QueryHistory.objects
            .filter(user=user, dataset_id=dataset_id, success=True, cached=False)
            .exclude(sql_generated='')
            .exclude(sql_generated__startswith='--')
            .order_by('-created_at')[:HISTORY_CONTEXT]
            .values('question', 'sql_generated')
        )
        return [
            {'question': item['question'], 'sql': item['sql_generated']}
            for item in reversed(list(recientes))
        ]
