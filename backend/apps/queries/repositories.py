# apps/queries/repositories.py
from .models import QueryHistory, QueryResult


class QueryRepository:

    @staticmethod
    def save_query(
        user,
        dataset_id:     int,
        question:       str,
        sql_generated:  str,
        execution_time: float,
        success:        bool,
        error_msg:      str,
        model_used:     str,
        retry_count:    int,
        cached:         bool,
    ) -> QueryHistory:
        return QueryHistory.objects.create(
            user           = user,
            dataset_id     = dataset_id,
            question       = question,
            sql_generated  = sql_generated,
            execution_time = execution_time,
            success        = success,
            error_msg      = error_msg,
            model_used     = model_used,
            retry_count    = retry_count,
            cached         = cached,
        )

    @staticmethod
    def save_result(
        query:        QueryHistory,
        rows:         list,
        columns:      list,
        chart_type:   str,
        chart_config: dict = None,
    ) -> QueryResult:
        return QueryResult.objects.create(
            query       = query,
            result_json = rows,
            columns     = columns,
            row_count   = len(rows),
            chart_type  = chart_type,
            chart_config = chart_config or QueryRepository._build_chart_config(chart_type, rows, columns),
        )

    @staticmethod
    def _build_chart_config(chart_type: str, rows: list, columns: list) -> dict:
        """
        Genera la config básica de Recharts según el tipo de gráfica.
        El frontend puede usarla directamente o sobreescribirla.
        """
        if not rows or not columns:
            return {}

        num_cols  = [c['name'] for c in columns if c['dtype'] in ('int', 'float')]
        cat_cols  = [c['name'] for c in columns if c['dtype'] == 'str']
        date_cols = [c['name'] for c in columns if c['dtype'] == 'date']

        x_key = date_cols[0] if date_cols else (cat_cols[0] if cat_cols else columns[0]['name'])
        y_key = num_cols[0]  if num_cols  else columns[-1]['name']

        configs = {
            'bar':     {'xKey': x_key, 'yKey': y_key, 'legend': True},
            'line':    {'xKey': x_key, 'yKey': y_key, 'dot': False},
            'pie':     {'nameKey': x_key, 'valueKey': y_key},
            'scatter': {'xKey': num_cols[0] if num_cols else x_key,
                        'yKey': num_cols[1] if len(num_cols) > 1 else y_key},
            'table':   {'columns': [c['name'] for c in columns]},
            # Análisis: el engine normalmente trae su propia config;
            # estos son respaldos coherentes con lo que retorna
            'forecast': {'xKey': x_key, 'yKey': y_key, 'splitKey': 'tipo'},
            'anomaly':  {'xKey': num_cols[0] if num_cols else x_key,
                         'yKey': num_cols[1] if len(num_cols) > 1 else y_key},
            'segment':  {'xKey': num_cols[0] if num_cols else x_key,
                         'yKey': num_cols[1] if len(num_cols) > 1 else y_key,
                         'segmentKey': 'segmento'},
            'drivers':  {'xKey': y_key, 'yKey': x_key},
        }
        return configs.get(chart_type, {})