# apps/queries/services/query_service.py
import time

from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import NotFound, ValidationError

from apps.dataset.models import Dataset
from apps.dataset.repositories import DatasetRepository
from apps.users.services import UserService
from services.ai import AIQueryService
from services.analysis import AnalysisService, detect as detect_analysis
from ..repositories import QueryRepository
from .cache_service import CacheService


class QueryService:
    """
    Único punto de contacto entre la app queries y el AI engine.
    Responsabilidades:
      1. Dataset — valida existencia y estado READY
      2. Caché — evita llamar al LLM para preguntas repetidas
      3. AI engine — delega toda la lógica de LLM a AIQueryService
      4. Persistencia — guarda el resultado via QueryRepository (atómica)
      5. Cuota — actualiza el contador del usuario (también en hits de caché)
    """

    @staticmethod
    def execute(question: str, dataset_id: int, user) -> dict:

        # 1. Dataset — debe existir y estar listo para consultas
        try:
            dataset = DatasetRepository.get_by_id(dataset_id)
        except Dataset.DoesNotExist:
            raise NotFound('Dataset no encontrado.')

        if dataset.status != Dataset.Status.READY:
            raise ValidationError(
                {'dataset_id': f'El dataset no está listo para consultas (estado: {dataset.status}).'}
            )

        version = dataset.updated_at.isoformat()

        # 2. Caché
        cached = CacheService.get(question, dataset_id, version)
        if cached:
            return QueryService._cache_hit_response(cached, question, dataset_id, user)

        # 3. Anti-stampede — si otro worker ya calcula esta misma consulta,
        #    esperar a que llene el caché en vez de duplicar la llamada al LLM
        got_lock = CacheService.acquire_lock(question, dataset_id, version)
        if not got_lock:
            for _ in range(5):
                time.sleep(1)
                cached = CacheService.get(question, dataset_id, version)
                if cached:
                    return QueryService._cache_hit_response(cached, question, dataset_id, user)
            # Nadie llenó el caché: calculamos de todas formas (mejor duplicar que fallar)

        try:
            # 4. Motor: análisis estadístico si la intención lo pide
            #    (pronóstico/anomalías/segmentación/factores); si no, SQL con LLM
            analysis_type = detect_analysis(question)
            if analysis_type:
                engine_result = AnalysisService.execute(
                    analysis_type = analysis_type,
                    dataset_id    = dataset_id,
                    question      = question,
                )
            else:
                engine_result = AIQueryService.execute(
                    question   = question,
                    dataset_id = dataset_id,
                    schema     = dataset.schema_json,
                )

            # 5. Persistencia atómica — nunca queda un QueryHistory sin su QueryResult
            with transaction.atomic():
                query = QueryRepository.save_query(
                    user           = user,
                    dataset_id     = dataset_id,
                    question       = question,
                    sql_generated  = engine_result['sql'],
                    execution_time = engine_result['execution_time'],
                    success        = engine_result['success'],
                    error_msg      = engine_result['error_msg'],
                    model_used     = engine_result.get('model_used') or getattr(settings, 'OLLAMA_MODEL', ''),
                    retry_count    = engine_result['retry_count'],
                    cached         = False,
                )

                result = None
                if engine_result['success']:
                    result = QueryRepository.save_result(
                        query        = query,
                        rows         = engine_result['rows'],
                        columns      = engine_result['columns'],
                        chart_type   = engine_result['chart_type'],
                        chart_config = engine_result.get('chart_config'),
                    )

            # 6. Cuota
            UserService.increment_usage(user)

            # 7. Construye respuesta y cachea si fue exitosa
            response = QueryService._build_response(query, result, cached=False)
            if engine_result['success']:
                CacheService.set(question, dataset_id, response, version)

            return response
        finally:
            if got_lock:
                CacheService.release_lock(question, dataset_id, version)

    @staticmethod
    def _cache_hit_response(cached: dict, question: str, dataset_id: int, user) -> dict:
        """
        Los hits de caché también se persisten en el historial (cached=True)
        para no corromper las métricas del TFG, y cuentan para la cuota.
        El query_id devuelto es el del NUEVO registro, así el feedback
        se ancla a esta consulta y no a la original cacheada.
        """
        query = QueryRepository.save_query(
            user           = user,
            dataset_id     = dataset_id,
            question       = question,
            sql_generated  = cached.get('sql', ''),
            execution_time = 0.0,
            success        = True,
            error_msg      = '',
            model_used     = cached.get('model_used', ''),
            retry_count    = 0,
            cached         = True,
        )
        UserService.increment_usage(user)
        return {**cached, 'cached': True, 'query_id': query.id}

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
