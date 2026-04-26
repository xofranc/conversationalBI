import pandas as pd
import sqlite3
import os
from django.conf import settings


class SQLExecutor:

    @staticmethod
    def run(sql: str, dataset_id: int) -> tuple[list, list]:
        """
        Ejecuta el SQL contra el archivo del dataset.
        Retorna (rows, columns) donde:
          - rows:    lista de dicts [{col: val}, ...]
          - columns: lista de dicts [{name, dtype}]
        """
        from apps.dataset.repositories import DatasetRepository

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
        rows = df.to_dict(orient='records')

        return rows, columns

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