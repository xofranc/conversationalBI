# apps/queries/services/pipeline/engine_router.py
from .base import Middleware
from services.ai import AIQueryService
from services.analysis import AnalysisService, detect as detect_analysis
from ..repositories import QueryRepository

# How many previous queries to include as conversation context
HISTORY_CONTEXT = 3


class EngineRouter(Middleware):
    """Routes query to appropriate engine (statistical analysis or LLM)."""
    
    def process(self, context: dict) -> dict:
        question = context['question']
        dataset_id = context['dataset_id']
        dataset = context['dataset']
        user = context['user']
        
        # Detect if statistical analysis is needed
        analysis_type = detect_analysis(question)
        
        if analysis_type:
            # Statistical analysis engine
            engine_result = AnalysisService.execute(
                analysis_type=analysis_type,
                dataset_id=dataset_id,
                question=question,
            )
        else:
            # LLM engine with conversation context
            history = self._conversation_context(user, dataset_id)
            engine_result = AIQueryService.execute(
                question=question,
                dataset_id=dataset_id,
                schema=dataset.schema_json,
                history=history,
            )
        
        context['engine_result'] = engine_result
        return context
    
    def _conversation_context(self, user, dataset_id: int) -> list:
        """Get recent successful queries for conversation context."""
        from ..models import QueryHistory
        
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
