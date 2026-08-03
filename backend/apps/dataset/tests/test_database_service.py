# apps/dataset/tests/test_database_service.py
import pandas as pd
import pytest

from apps.dataset.services import DatabaseService
from conftest import requires_postgres

pytestmark = requires_postgres


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


@pytest.fixture
def schema_creado(csv_file):
    schema = DatabaseService.materialize(dataset_id=99, abs_file_path=csv_file)
    yield schema
    DatabaseService.delete(schema)


class TestDatabaseService:

    def test_materialize_crea_schema_consultable(self, schema_creado):
        assert schema_creado == 'ds_99'
        assert DatabaseService.exists(schema_creado)

        tables = DatabaseService.read_tables(schema_creado)
        assert list(tables) == ['main']
        assert len(tables['main']) == 3

    def test_conexion_es_solo_lectura(self, schema_creado):
        conn = DatabaseService.connect_readonly(schema_creado)
        try:
            with conn.cursor() as cur:
                # Leer funciona (rol bi_reader con GRANT SELECT al materializar)
                cur.execute('SELECT COUNT(*) FROM main')
                assert cur.fetchone()[0] == 3
                # Escribir, no: sesión read-only + rol sin privilegios de escritura
                with pytest.raises(Exception):
                    cur.execute('DROP TABLE main')
        finally:
            conn.close()

    def test_delete_elimina_el_schema(self, csv_file):
        schema = DatabaseService.materialize(dataset_id=97, abs_file_path=csv_file)
        DatabaseService.delete(schema)
        assert not DatabaseService.exists(schema)

    def test_delete_tolerante_a_ruta_vacia(self):
        DatabaseService.delete('')  # no lanza

    def test_exists_rechaza_rutas_legacy_sin_conectar(self):
        # Rutas de la era SQLite no son schemas: False sin tocar la red
        assert not DatabaseService.exists('dbs/dataset_3.sqlite')
        assert not DatabaseService.exists('')
