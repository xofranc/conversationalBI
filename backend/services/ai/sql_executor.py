import pandas as pd
import sqlite3
import os
from django.conf import settings

from apps.dataset.services.schema_service import SchemaService


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
        Carga las tablas del archivo en SQLite en memoria usando el
        loader compartido (SchemaService.read_tables): las tablas del
        sandbox coinciden exactamente con las del schema_json.
        """
        conn = sqlite3.connect(':memory:')
        for name, df in SchemaService.read_tables(file_path, ext).items():
            df.to_sql(name, conn, index=False, if_exists='replace')
        return conn

    @staticmethod
    def _dtype(series: pd.Series) -> str:
        # Misma heurística que el schema (incluye detección de fechas):
        # un `date` del schema sigue siendo `date` tras el roundtrip por SQLite
        return SchemaService.infer_dtype(series)