import os
import re

import pandas as pd
import psycopg2
from psycopg2 import sql as pgsql
from psycopg2.extras import execute_values
from django.conf import settings

from .schema_service import SchemaService

_SCHEMA_RE = re.compile(r'^[a-z_][a-z0-9_]*$')


class DatabaseService:
    """
    Materializa el archivo del dataset (CSV/Excel/JSON) en un schema
    Postgres propio por dataset: ds_<id>, con una tabla por hoja/archivo.

    Así las consultas no releen ni reconvierten el archivo original en
    cada pregunta: las tablas quedan en Postgres y se leen con un rol
    de solo-lectura (bi_reader) como defensa en profundidad.

    Dataset.db_path guarda el nombre del schema ('ds_12'), no una ruta.
    """

    @staticmethod
    def materialize(dataset_id: int, abs_file_path: str) -> str:
        """
        Convierte el archivo del dataset a tablas Postgres en su schema.
        Retorna el nombre del schema (para Dataset.db_path).
        """
        ext = os.path.splitext(abs_file_path)[1].lower()
        tables = SchemaService.read_tables(abs_file_path, ext)

        schema = DatabaseService.schema_name(dataset_id)
        conn = psycopg2.connect(settings.DATABASE_URL)
        conn.autocommit = True
        try:
            with conn.cursor() as cur:
                cur.execute(pgsql.SQL('CREATE SCHEMA IF NOT EXISTS {}').format(pgsql.Identifier(schema)))
                for name, df in tables.items():
                    clean = name.replace('.', '_')
                    cols_def = pgsql.SQL(', ').join(
                        pgsql.SQL('{} {}').format(
                            pgsql.Identifier(str(c)),
                            pgsql.SQL(DatabaseService._pg_type(df[c])),
                        )
                        for c in df.columns
                    )
                    table = pgsql.Identifier(schema, clean)
                    cur.execute(pgsql.SQL('DROP TABLE IF EXISTS {}').format(table))
                    cur.execute(pgsql.SQL('CREATE TABLE {} ({})').format(table, cols_def))
                    if len(df) > 0:
                        cols_list = pgsql.SQL(', ').join(pgsql.Identifier(str(c)) for c in df.columns)
                        rows = [
                            tuple(DatabaseService._py(v) for v in row)
                            for row in df.itertuples(index=False, name=None)
                        ]
                        execute_values(
                            cur,
                            pgsql.SQL('INSERT INTO {} ({}) VALUES %s').format(table, cols_list).as_string(conn),
                            rows,
                        )
                DatabaseService._grant_reader(cur, schema)
        finally:
            conn.close()

        return schema

    @staticmethod
    def schema_name(dataset_id: int) -> str:
        return f'ds_{dataset_id}'

    @staticmethod
    def exists(db_path: str) -> bool:
        """True si db_path es un schema materializado que sigue existiendo."""
        if not db_path or not _SCHEMA_RE.match(db_path):
            return False
        conn = psycopg2.connect(settings.DATABASE_URL)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT 1 FROM information_schema.schemata WHERE schema_name = %s',
                    [db_path],
                )
                return cur.fetchone() is not None
        finally:
            conn.close()

    @staticmethod
    def connect_readonly(db_path: str):
        """
        Conexión de solo-lectura con search_path al schema del dataset:
        aunque el SQL envuelto falle en la validación, el rol bi_reader
        (y la sesión read-only) impiden escribir (defensa en profundidad).
        """
        if not db_path or not _SCHEMA_RE.match(db_path):
            raise ValueError(f'Schema de dataset inválido: {db_path!r}')
        dsn = settings.DATABASE_READER_URL or settings.DATABASE_URL
        conn = psycopg2.connect(dsn)
        conn.set_session(autocommit=True, readonly=True)
        with conn.cursor() as cur:
            cur.execute(
                pgsql.SQL('SET search_path TO {}').format(pgsql.Identifier(db_path))
            )
        return conn

    @staticmethod
    def read_tables(db_path: str) -> dict:
        """
        {nombre_tabla: DataFrame} leído del schema del dataset.
        Equivalente a SchemaService.read_tables sobre el archivo original:
        las fechas vuelven como texto/timestamp y el engine las re-parsea.
        """
        conn = DatabaseService.connect_readonly(db_path)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT table_name FROM information_schema.tables '
                    'WHERE table_schema = %s ORDER BY table_name',
                    [db_path],
                )
                names = [row[0] for row in cur.fetchall()]
            return {
                name: pd.read_sql_query(
                    pgsql.SQL('SELECT * FROM {}').format(pgsql.Identifier(db_path, name)).as_string(conn),
                    conn,
                )
                for name in names
            }
        finally:
            conn.close()

    @staticmethod
    def delete(db_path: str) -> None:
        """Elimina el schema materializado (fallo aquí es recuperable)."""
        if not db_path:
            return
        if _SCHEMA_RE.match(db_path):
            conn = psycopg2.connect(settings.DATABASE_URL)
            conn.autocommit = True
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        pgsql.SQL('DROP SCHEMA IF EXISTS {} CASCADE').format(pgsql.Identifier(db_path))
                    )
            finally:
                conn.close()
        else:
            # Dataset legacy con BD SQLite en disco: limpieza del archivo
            abs_path = os.path.join(settings.MEDIA_ROOT, db_path)
            if os.path.exists(abs_path):
                os.remove(abs_path)

    # ── Internos ─────────────────────────────────────────────────────

    @staticmethod
    def _pg_type(series: pd.Series) -> str:
        dt = str(series.dtype)
        if dt.startswith('int'):
            return 'BIGINT'
        if dt.startswith('float'):
            return 'DOUBLE PRECISION'
        if dt == 'bool':
            return 'BOOLEAN'
        if dt.startswith('datetime64'):
            return 'TIMESTAMP'
        return 'TEXT'

    @staticmethod
    def _py(val):
        """Normaliza valores de pandas/numpy a tipos que psycopg2 adapta."""
        if val is None or pd.isna(val):
            return None
        if hasattr(val, 'item'):        # numpy int64, float64, bool_
            return val.item()
        return val

    @staticmethod
    def _grant_reader(cur, schema: str) -> None:
        """Concede SELECT al rol lector sobre el schema recién materializado,
        solo si el rol existe en el servidor (defensa en profundidad activa)."""
        role = getattr(settings, 'DATABASE_READER_ROLE', '')
        if not role or not _SCHEMA_RE.match(role):
            return
        cur.execute('SELECT 1 FROM pg_roles WHERE rolname = %s', [role])
        if cur.fetchone() is None:
            return
        cur.execute(
            pgsql.SQL('GRANT USAGE ON SCHEMA {} TO {}').format(
                pgsql.Identifier(schema), pgsql.Identifier(role),
            )
        )
        cur.execute(
            pgsql.SQL('GRANT SELECT ON ALL TABLES IN SCHEMA {} TO {}').format(
                pgsql.Identifier(schema), pgsql.Identifier(role),
            )
        )
