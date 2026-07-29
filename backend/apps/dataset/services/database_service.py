import os
import sqlite3

import pandas as pd
from django.conf import settings

from .schema_service import SchemaService


class DatabaseService:
    """
    Materializa el archivo del dataset (CSV/Excel/JSON) en una base de
    datos SQLite persistente por dataset: media/dbs/dataset_<id>.sqlite

    Así las consultas no releen ni reconvierten el archivo original en
    cada pregunta: la BD queda almacenada y se abre en modo solo-lectura.
    """

    DBS_DIR = 'dbs'

    @staticmethod
    def materialize(dataset_id: int, abs_file_path: str) -> str:
        """
        Convierte el archivo del dataset a SQLite en disco.
        Retorna la ruta de la BD relativa a MEDIA_ROOT (para Dataset.db_path).
        """
        ext = os.path.splitext(abs_file_path)[1].lower()
        tables = SchemaService.read_tables(abs_file_path, ext)

        rel_path = DatabaseService.relative_path(dataset_id)
        abs_path = os.path.join(settings.MEDIA_ROOT, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)

        # Si existía una materialización anterior (re-subida), se reemplaza
        if os.path.exists(abs_path):
            os.remove(abs_path)

        conn = sqlite3.connect(abs_path)
        try:
            for name, df in tables.items():
                df.to_sql(name, conn, index=False, if_exists='replace')
            conn.commit()
        finally:
            conn.close()

        return rel_path

    @staticmethod
    def relative_path(dataset_id: int) -> str:
        return os.path.join(DatabaseService.DBS_DIR, f'dataset_{dataset_id}.sqlite')

    @staticmethod
    def abs_path(db_path: str) -> str:
        return os.path.join(settings.MEDIA_ROOT, db_path)

    @staticmethod
    def exists(db_path: str) -> bool:
        return bool(db_path) and os.path.exists(DatabaseService.abs_path(db_path))

    @staticmethod
    def connect_readonly(db_path: str) -> sqlite3.Connection:
        """
        Conexión solo-lectura vía URI: imposible escribir aunque el SQL
        envuelto falle en la validación (defensa en profundidad).
        """
        abs_path = DatabaseService.abs_path(db_path)
        uri = f'file:{abs_path}?mode=ro'
        return sqlite3.connect(uri, uri=True)

    @staticmethod
    def read_tables(db_path: str) -> dict:
        """
        {nombre_tabla: DataFrame} leído de la BD persistida.
        Equivalente a SchemaService.read_tables sobre el archivo original:
        las fechas vuelven como texto ISO y el engine las re-parsea,
        igual que tras el roundtrip del sandbox en memoria.
        """
        conn = DatabaseService.connect_readonly(db_path)
        try:
            names = [
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
                    "ORDER BY name"
                )
            ]
            return {
                name: pd.read_sql_query(f'SELECT * FROM "{name}"', conn)
                for name in names
            }
        finally:
            conn.close()

    @staticmethod
    def delete(db_path: str) -> None:
        """Elimina la BD materializada (fallo aquí es recuperable)."""
        if not db_path:
            return
        abs_path = DatabaseService.abs_path(db_path)
        if os.path.exists(abs_path):
            os.remove(abs_path)
