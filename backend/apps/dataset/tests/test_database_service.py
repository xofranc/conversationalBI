# apps/dataset/tests/test_database_service.py
import sqlite3

import pandas as pd
import pytest

from apps.dataset.services import DatabaseService


@pytest.fixture
def csv_file(tmp_path, settings):
    """CSV de prueba en un MEDIA_ROOT temporal."""
    settings.MEDIA_ROOT = str(tmp_path)
    df = pd.DataFrame({
        'ciudad': ['Bogotá', 'Cali', 'Bogotá'],
        'monto': [100.0, 200.0, 150.0],
    })
    df.to_csv(tmp_path / 'ventas.csv', index=False)
    return str(tmp_path / 'ventas.csv')


class TestDatabaseService:

    def test_materialize_crea_bd_consultable(self, csv_file):
        rel_path = DatabaseService.materialize(dataset_id=99, abs_file_path=csv_file)

        assert rel_path.endswith('dataset_99.sqlite')
        assert DatabaseService.exists(rel_path)

        tables = DatabaseService.read_tables(rel_path)
        assert list(tables) == ['main']
        assert len(tables['main']) == 3

    def test_conexion_es_solo_lectura(self, csv_file):
        rel_path = DatabaseService.materialize(dataset_id=98, abs_file_path=csv_file)

        conn = DatabaseService.connect_readonly(rel_path)
        # Leer funciona
        assert conn.execute('SELECT COUNT(*) FROM main').fetchone()[0] == 3
        # Escribir, no
        with pytest.raises(sqlite3.OperationalError):
            conn.execute('DROP TABLE main')
        conn.close()

    def test_delete_elimina_la_bd(self, csv_file):
        rel_path = DatabaseService.materialize(dataset_id=97, abs_file_path=csv_file)
        DatabaseService.delete(rel_path)
        assert not DatabaseService.exists(rel_path)

    def test_delete_tolerante_a_ruta_vacia(self):
        DatabaseService.delete('')  # no lanza
