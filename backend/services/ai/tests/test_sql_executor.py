# services/ai/tests/test_sql_executor.py
import numpy as np
import pandas as pd
import pytest

from apps.dataset.models import Dataset
from services.ai.sql_executor import SQLExecutor

pytestmark = pytest.mark.django_db


@pytest.fixture
def csv_dataset(test_user, tmp_path, settings):
    """Dataset READY con un CSV real de 5 filas en un MEDIA_ROOT temporal."""
    settings.MEDIA_ROOT = str(tmp_path)
    (tmp_path / 'ventas.csv').write_text(
        'ciudad,monto\n'
        'Bogota,100.5\n'
        'Cali,200.0\n'
        'Medellin,150.0\n'
        'Cali,80.0\n'
        'Bogota,300.0\n'
    )
    return Dataset.objects.create(
        user=test_user,
        name='ventas',
        file_path='ventas.csv',
        status=Dataset.Status.READY,
        schema_json={'tables': [{'name': 'main', 'row_count': 5, 'columns': []}]},
    )


class TestLimiteDuro:

    def test_sql_sin_limit_se_trunca_a_max_rows(self, csv_dataset, monkeypatch):
        monkeypatch.setattr(SQLExecutor, 'MAX_ROWS', 2)
        rows, _ = SQLExecutor.run('SELECT * FROM main', csv_dataset.id)
        assert len(rows) == 2

    def test_limit_interno_mayor_no_elude_el_tope(self, csv_dataset, monkeypatch):
        monkeypatch.setattr(SQLExecutor, 'MAX_ROWS', 2)
        rows, _ = SQLExecutor.run('SELECT * FROM main LIMIT 999', csv_dataset.id)
        assert len(rows) == 2

    def test_limit_interno_menor_se_respeta(self, csv_dataset):
        rows, _ = SQLExecutor.run('SELECT * FROM main LIMIT 1', csv_dataset.id)
        assert len(rows) == 1

    def test_columna_con_limit_en_el_nombre_no_rompe_nada(self, csv_dataset):
        # Regresión del bug de subcadena "limit": antes suprimía el LIMIT
        rows, _ = SQLExecutor.run(
            'SELECT ciudad, monto FROM main ORDER BY monto DESC', csv_dataset.id
        )
        assert len(rows) == 5
        assert rows[0]['monto'] == 300.0


class TestNormalizacionJSON:

    def test_nan_se_convierte_a_none(self):
        assert SQLExecutor._json_safe(float('nan')) is None
        assert SQLExecutor._json_safe(pd.NaT) is None
        assert SQLExecutor._json_safe(None) is None

    def test_timestamp_se_convierte_a_isoformat(self):
        assert SQLExecutor._json_safe(pd.Timestamp('2024-01-15')) == '2024-01-15T00:00:00'

    def test_numpy_se_convierte_a_nativo(self):
        assert SQLExecutor._json_safe(np.int64(5)) == 5
        assert SQLExecutor._json_safe(np.float64(1.5)) == 1.5

    def test_rows_son_json_serializables(self, csv_dataset):
        import json
        rows, columns = SQLExecutor.run('SELECT * FROM main', csv_dataset.id)
        json.dumps(rows)      # no debe lanzar TypeError
        json.dumps(columns)


class TestJSONMultiTabla:
    """El sandbox carga las mismas tablas que promete el schema (loader compartido)."""

    @pytest.fixture
    def json_dataset(self, test_user, tmp_path, settings):
        import json as json_lib
        settings.MEDIA_ROOT = str(tmp_path)
        (tmp_path / 'tienda.json').write_text(json_lib.dumps({
            'ventas':    [{'ciudad': 'Bogota', 'monto': 100}, {'ciudad': 'Cali', 'monto': 50}],
            'productos': [{'nombre': 'A', 'precio': 10}],
        }))
        return Dataset.objects.create(
            user=test_user,
            name='tienda',
            file_path='tienda.json',
            status=Dataset.Status.READY,
            schema_json={'tables': [
                {'name': 'ventas', 'row_count': 2, 'columns': []},
                {'name': 'productos', 'row_count': 1, 'columns': []},
            ]},
        )

    def test_ambas_tablas_son_consultables(self, json_dataset):
        rows, _ = SQLExecutor.run('SELECT * FROM ventas WHERE ciudad = "Cali"', json_dataset.id)
        assert rows == [{'ciudad': 'Cali', 'monto': 50}]

        rows, _ = SQLExecutor.run('SELECT nombre FROM productos', json_dataset.id)
        assert rows == [{'nombre': 'A'}]
