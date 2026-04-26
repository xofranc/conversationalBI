import time
from .prompt_builder import PromptBuilder
from .sql_agent import SQLAgent
from .sql_validator import SQLValidator
from .sql_executor import SQLExecutor
from .chart_selector import ChartSelector

MAX_RETRIES = 3


class AIQueryService:
    """
    Orquestador del AI engine. No sabe nada de Django ORM,
    no importa modelos, no toca la BD de la app.
    Recibe el schema como dict y retorna un dict con el resultado.
    """

    @staticmethod
    def execute(question: str, dataset_id: int, schema: dict) -> dict:
        agent       = SQLAgent()
        prompt      = PromptBuilder.build(question, schema)
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

                if sql.strip() == 'NO_SQL_POSSIBLE':
                    error_msg = 'El modelo indicó que no puede responder con el esquema dado.'
                    break

                SQLValidator.assert_safe(sql)
                rows, columns = SQLExecutor.run(sql, dataset_id)
                success     = True
                retry_count = attempt
                break

            except Exception as e:
                error_msg   = str(e)
                retry_count = attempt + 1
                prompt      = PromptBuilder.build_correction(
                    question     = question,
                    schema       = schema,
                    previous_sql = sql,
                    error        = error_msg,
                )

        chart_type = ChartSelector.pick(columns, rows) if success else 'table'

        return {
            'sql':            sql,
            'success':        success,
            'error_msg':      error_msg,
            'retry_count':    retry_count,
            'execution_time': round(time.time() - start, 3),
            'rows':           rows,
            'columns':        columns,
            'chart_type':     chart_type,
        }