# services/analysis/analysis_service.py
"""
Fachada Django del motor de análisis: carga las tablas del schema Postgres
del dataset (DatabaseService.read_tables — la misma fuente que el SQL de la
consola) y delega el cómputo al engine puro.

Retorna el mismo contrato que AIQueryService.execute + chart_config y
method, para que QueryService no distinga un motor del otro.
"""
import logging
import time

from apps.dataset.services.database_service import DatabaseService
from services.ai.answer_writer import AnswerWriter
from services.ai.suggester import suggest

from . import engine, intent

logger = logging.getLogger(__name__)

_MODEL_LABELS = {
    intent.FORECAST: 'análisis:pronóstico',
    intent.ANOMALY:  'análisis:anomalías',
    intent.SEGMENT:  'análisis:segmentación',
    intent.DRIVERS:  'análisis:factores',
    intent.SUMMARY:  'análisis:resumen',
}


class AnalysisService:

    @staticmethod
    def execute(analysis_type: str, dataset_id: int, question: str) -> dict:
        start = time.time()

        # Import local: mismo patrón que SQLExecutor (evita acoplar el
        # módulo a Django en tiempo de importación)
        from apps.dataset.repositories import DatasetRepository
        dataset = DatasetRepository.get_by_id(dataset_id)

        # Las tablas se leen del schema Postgres del dataset (misma fuente
        # que el SQL de la consola); QueryService garantiza la materialización.
        tables = DatabaseService.read_tables(dataset.db_path)

        base = {
            'sql': '',
            'model_used': _MODEL_LABELS.get(analysis_type, f'análisis:{analysis_type}'),
            'retry_count': 0,
        }

        try:
            result = engine.run(analysis_type, tables, question)
        except engine.AnalysisError as e:
            return {
                **base,
                'success': False,
                'error_msg': str(e),
                'execution_time': round(time.time() - start, 3),
                'rows': [], 'columns': [], 'chart_type': 'table', 'chart_config': {},
                'answer': '', 'suggestions': suggest(dataset.schema_json),
            }
        except Exception as e:
            logger.exception('Fallo inesperado en análisis %s', analysis_type)
            return {
                **base,
                'success': False,
                'error_msg': 'El análisis falló de forma inesperada. Intenta con otra pregunta.',
                'execution_time': round(time.time() - start, 3),
                'rows': [], 'columns': [], 'chart_type': 'table', 'chart_config': {},
                'answer': '', 'suggestions': suggest(dataset.schema_json),
            }

        metodo = f"-- {result['method']}"
        answer = AnswerWriter().write(
            question, metodo, result['rows'], len(result['rows']),
        )

        return {
            **base,
            'success': True,
            'error_msg': '',
            'execution_time': round(time.time() - start, 3),
            'rows': result['rows'],
            'columns': result['columns'],
            'chart_type': result['chart_type'],
            'chart_config': result['chart_config'],
            # Recibo verificable: qué método estadístico produjo la figura
            'sql': metodo,
            'answer': answer,
            'suggestions': [],
        }
