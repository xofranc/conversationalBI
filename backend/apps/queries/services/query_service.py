# apps/queries/services/query_service.py
from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import NotFound, ValidationError

from apps.dataset.models import Dataset
from apps.dataset.repositories import DatasetRepository
from services.ai import AIQueryService
from ..repositories import QueryRepository
from .cache_service import CacheService


class QueryService:
    """
    Único punto de contacto entre la app queries y el AI engine.
    Responsabilidades:
      1. Caché — evita llamar al LLM para preguntas repetidas
      2. Schema — obtiene el esquema del dataset via DatasetRepository
      3. AI engine — delega toda la lógica de LLM a AIQueryService
      4. Persistencia — guarda el resultado via QueryRepository
      5. Cuota — actualiza el contador del usuario
    """

    @staticmethod
    def execute(question: str, dataset_id: int, user) -> dict:

        # 1. Caché
        cached = CacheService.get(question, dataset_id)
        if cached:
            return {**cached, 'cached': True}   # copia: no mutar el objeto cacheado

        # 2. Dataset — debe existir y estar listo para consultas
        try:
            dataset = DatasetRepository.get_by_id(dataset_id)
        except Dataset.DoesNotExist:
            raise NotFound('Dataset no encontrado.')

        if dataset.status != Dataset.Status.READY:
            raise ValidationError(
                {'dataset_id': f'El dataset no está listo para consultas (estado: {dataset.status}).'}
            )

        schema = dataset.schema_json

        # 3. AI engine — no sabe nada de Django
        ai_result = AIQueryService.execute(
            question   = question,
            dataset_id = dataset_id,
            schema     = schema,
        )

        # 4. Persistencia atómica — nunca queda un QueryHistory sin su QueryResult
        with transaction.atomic():
            query = QueryRepository.save_query(
                user           = user,
                dataset_id     = dataset_id,
                question       = question,
                sql_generated  = ai_result['sql'],
                execution_time = ai_result['execution_time'],
                success        = ai_result['success'],
                error_msg      = ai_result['error_msg'],
                model_used     = getattr(settings, 'OLLAMA_MODEL', ''),
                retry_count    = ai_result['retry_count'],
                cached         = False,
            )

            result = None
            if ai_result['success']:
                result = QueryRepository.save_result(
                    query      = query,
                    rows       = ai_result['rows'],
                    columns    = ai_result['columns'],
                    chart_type = ai_result['chart_type'],
                )

        # 5. Cuota
        from apps.users.services import UserService
        UserService.increment_usage(user)

        # 6. Construye respuesta y cachea si fue exitosa
        response = QueryService._build_response(query, result, cached=False)
        if ai_result['success']:
            CacheService.set(question, dataset_id, response)

        return response

    @staticmethod
    def _build_response(query, result, cached: bool) -> dict:
        return {
            'query_id':       query.id,
            'sql':            query.sql_generated,
            'success':        query.success,
            'error_msg':      query.error_msg,
            'execution_time': query.execution_time,
            'model_used':     query.model_used,
            'retry_count':    query.retry_count,
            'cached':         cached,
            'data':           result.result_json if result else [],
            'columns':        result.columns     if result else [],
            'chart_type':     result.chart_type  if result else 'table',
            'chart_config':   result.chart_config if result else {},
            'row_count':      result.row_count   if result else 0,
        }