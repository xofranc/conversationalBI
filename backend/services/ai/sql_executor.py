import pandas as pd
import sqlite3
import os
from django.conf import settings


class SQLExecutor:

    MAX_ROWS = 1000  
    
    @staticmethod
    def run(sql: str, dataset_id: int) -> tuple[list, list]:
        """
        Ejecuta el SQL contra el archivo del dataset.
        Retorna (rows, columns) donde:
          - rows:    lista de dicts [{col: val}, ...]
          - columns: lista de dicts [{name, dtype}]
        """
        
        from apps.dataset.repositories import DatasetRepository

        # Límite duro e ineludible: el SQL del LLM se envuelve como subquery.
        # Funciona aunque el SQL interno tenga su propio LIMIT (gana el menor)
        # y no depende de detectar la palabra "limit" como subcadena.
        sql = sql.strip().rstrip(';')
        sql = f'SELECT * FROM ({sql}) LIMIT {SQLExecutor.MAX_ROWS}'

        dataset   = DatasetRepository.get_by_id(dataset_id)
        file_path = os.path.join(settings.MEDIA_ROOT, dataset.file_path)
        ext       = os.path.splitext(file_path)[1].lower()

        # Carga el archivo en SQLite en memoria
        conn = SQLExecutor._load_into_sqlite(file_path, ext, dataset.schema_json)

        try:
            df = pd.read_sql_query(sql, conn)
        except Exception as e:
            raise ValueError(f"Error ejecutando SQL: {e}")
        finally:
            conn.close()

        columns = [
            {'name': col, 'dtype': SQLExecutor._dtype(df[col])}
            for col in df.columns
        ]
        rows = [
            {k: SQLExecutor._json_safe(v) for k, v in row.items()}
            for row in df.to_dict(orient='records')
        ]

        return rows, columns

    @staticmethod
    def _json_safe(val):
        """Normaliza valores de pandas/numpy a tipos JSON-serializables."""
        if val is None or pd.isna(val):
            return None                      # NaN / NaT → null
        if hasattr(val, 'isoformat'):        # Timestamp, datetime, date
            return val.isoformat()
        if hasattr(val, 'item'):             # numpy int64, float64, bool_
            return val.item()
        return val

    @staticmethod
    def _load_into_sqlite(file_path: str, ext: str,
                           schema_json: dict) -> sqlite3.Connection:
        """
        Lee el archivo con Pandas y lo carga en SQLite en memoria.
        Cada hoja/tabla del schema se convierte en una tabla SQLite.
        """
        conn = sqlite3.connect(':memory:')

        if ext == '.csv':
            df = pd.read_csv(file_path)
            table_name = schema_json.get('tables', [{}])[0].get('name', 'main')
            df.to_sql(table_name, conn, index=False, if_exists='replace')
        elif ext == '.json':
            df = pd.read_json(file_path)
            if isinstance(df, dict):
                for k, v in df.items():
                    pd.DataFrame(v).to_sql(k, conn, index=False, if_exists='replace')
            else:
                df.to_sql('main', conn, index=False, if_exists='replace')
                
        else: 
            xls = pd.ExcelFile(file_path)
            for sheet in xls.sheet_names:
                df = xls.parse(sheet)
                df.to_sql(sheet, conn, index=False, if_exists='replace')
        return conn

    @staticmethod
    def _dtype(series: pd.Series) -> str:
        kind = series.dtype.kind
        return {'i': 'int', 'u': 'int', 'f': 'float',
                'b': 'bool', 'M': 'date'}.get(kind, 'str')