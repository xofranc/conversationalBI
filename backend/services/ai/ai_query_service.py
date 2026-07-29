import logging
import time
from .prompt_builder import PromptBuilder
from .sql_agent import SQLAgent
from .sql_validator import SQLValidator, SecurityError
from .sql_executor import SQLExecutor
from .chart_selector import ChartSelector
from .answer_writer import AnswerWriter
from .suggester import suggest

MAX_RETRIES = 3

logger = logging.getLogger(__name__)


class _EmptyResult(Exception):
    """SQL válido pero con 0 filas: se reintenta con pistas de valores."""


class AIQueryService:
    """
    Orquestador del AI engine. No sabe nada de Django ORM,
    no importa modelos, no toca la BD de la app.
    Recibe el schema como dict y retorna un dict con el resultado.

    history: últimas consultas exitosas de la conversación
    [{'question': ..., 'sql': ...}, ...] para preguntas de seguimiento.
    """

    @staticmethod
    def execute(question: str, dataset_id: int, schema: dict,
                history: list | None = None) -> dict:
        agent       = SQLAgent()
        writer      = AnswerWriter()
        prompt      = PromptBuilder.build(question, schema, history)
        sql         = ''
        error_msg   = ''
        retry_count = 0
        success     = False
        rows        = []
        columns     = []

        start = time.time()

        for attempt in range(MAX_RETRIES):
            try:
                sql = agent.run(prompt)

                if sql.strip().startswith('NO_SQL_POSSIBLE'):
                    error_msg = 'Esa pregunta no se puede responder con las columnas de esta fuente.'
                    break

                SQLValidator.assert_safe(sql)
                rows, columns = SQLExecutor.run(sql, dataset_id)

                # Resultado vacío: tan fallo para el usuario como un error.
                # Se reintenta con los valores de ejemplo del esquema.
                if not rows and attempt < MAX_RETRIES - 1:
                    raise _EmptyResult('La consulta devolvió 0 filas.')

                success     = True
                retry_count = attempt
                break

            except SecurityError as e:
                # Violación de seguridad: fail-fast, sin reintentos ni gasto de LLM
                logger.warning('SQL rechazado por seguridad: %s', e)
                error_msg   = str(e)
                retry_count = attempt
                break

            except _EmptyResult as e:
                logger.info('Intento %d/%d sin filas, reintentando con pistas', attempt + 1, MAX_RETRIES)
                error_msg   = str(e)
                retry_count = attempt + 1
                prompt      = PromptBuilder.build_empty_result(
                    question     = question,
                    schema       = schema,
                    previous_sql = sql,
                )

            except Exception as e:
                logger.warning('Intento %d/%d falló: %s', attempt + 1, MAX_RETRIES, e)
                error_msg   = str(e)
                retry_count = attempt + 1
                prompt      = PromptBuilder.build_correction(
                    question     = question,
                    schema       = schema,
                    previous_sql = sql,
                    error        = error_msg,
                )

        selection = ChartSelector.select(columns, rows) if success else {
            'chart_type': 'table', 'chart_config': {},
        }

        # La conversación no muere en el error: siempre hay caminos
        answer = ''
        suggestions = []
        if success:
            answer = writer.write(question, sql, rows, len(rows))
        else:
            suggestions = suggest(schema)

        return {
            'sql':            sql,
            'success':        success,
            'error_msg':      error_msg,
            'retry_count':    retry_count,
            'execution_time': round(time.time() - start, 3),
            'rows':           rows,
            'columns':        columns,
            'chart_type':     selection['chart_type'],
            'chart_config':   selection['chart_config'],
            'answer':         answer,
            'suggestions':    suggestions,
        }
