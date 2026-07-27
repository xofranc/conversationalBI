# services/analysis/tests/test_analysis_service.py
from unittest.mock import patch

import pandas as pd
import pytest

from apps.dataset.models import Dataset
from apps.queries.models import QueryHistory
from apps.queries.services.query_service import QueryService
from services.analysis import AnalysisService, engine

pytestmark = pytest.mark.django_db


@pytest.fixture
def csv_mensual(test_user, tmp_path, settings):
    """Dataset READY con 24 meses de ventas en un MEDIA_ROOT temporal."""
    settings.MEDIA_ROOT = str(tmp_path)
    fechas = pd.date_range('2023-01-31', periods=24, freq='ME').strftime('%Y-%m-%d')
    df = pd.DataFrame({
        'fecha': fechas,
        'monto': [100.0 + 5 * i for i in range(24)],
        'cantidad': [10 + i % 3 for i in range(24)],
    })
    df.to_csv(tmp_path / 'ventas.csv', index=False)
    return Dataset.objects.create(
        user=test_user,
        name='ventas',
        file_path='ventas.csv',
        status=Dataset.Status.READY,
        schema_json={'tables': [{'name': 'main', 'row_count': 24, 'columns': []}]},
    )


class TestAnalysisService:

    def test_forecast_end_to_end(self, csv_mensual):
        res = AnalysisService.execute('forecast', csv_mensual.id, 'pronóstico de monto')

        assert res['success'] is True
        assert res['chart_type'] == 'forecast'
        assert res['model_used'] == 'análisis:pronóstico'
        assert res['sql'].startswith('--')          # recibo verificable del método
        assert res['chart_config']['yKey'] == 'monto'
        assert len(res['rows']) == 24 + 6

    def test_error_de_negocio_es_consulta_fallida_no_excepcion(self, test_user, tmp_path, settings):
        """Dataset sin fechas: el forecast responde con fallo en español, no con 500."""
        settings.MEDIA_ROOT = str(tmp_path)
        (tmp_path / 'sin_fechas.csv').write_text('ciudad,monto\nBogotá,100\nCali,200\n')
        ds = Dataset.objects.create(
            user=test_user, name='sf', file_path='sin_fechas.csv',
            status=Dataset.Status.READY,
            schema_json={'tables': [{'name': 'main', 'row_count': 2, 'columns': []}]},
        )
        res = AnalysisService.execute('forecast', ds.id, 'pronóstico')

        assert res['success'] is False
        assert 'fechas' in res['error_msg']
        assert res['rows'] == []

    def test_excepcion_inesperada_se_reporta_como_fallo(self, csv_mensual):
        with patch('services.analysis.analysis_service.engine.run', side_effect=RuntimeError('boom')):
            res = AnalysisService.execute('forecast', csv_mensual.id, 'pronóstico')
        assert res['success'] is False
        assert 'inesperada' in res['error_msg']


class TestIntegracionQueryService:
    """El dispatch vive en QueryService: análisis o SQL según la intención."""

    def test_pregunta_de_pronostico_no_llama_al_llm(self, test_user, csv_mensual):
        with patch('apps.queries.services.query_service.AIQueryService.execute') as mock_ai:
            res = QueryService.execute('¿qué monto se espera los próximos meses?', csv_mensual.id, test_user)

        mock_ai.assert_not_called()
        assert res['success'] is True
        assert res['chart_type'] == 'forecast'
        assert res['row_count'] == 30
        assert {r['tipo'] for r in res['data']} == {'real', 'pronóstico'}

    def test_analisis_se_persiste_en_el_historial(self, test_user, csv_mensual):
        QueryService.execute('¿hay anomalías en el monto?', csv_mensual.id, test_user)

        registro = QueryHistory.objects.get()
        assert registro.model_used == 'análisis:anomalías'
        assert registro.success is True
        assert registro.result.chart_type == 'anomaly'

    def test_pregunta_sql_normal_sigue_por_el_llm(self, test_user, csv_mensual):
        with patch('apps.queries.services.query_service.AIQueryService.execute') as mock_ai:
            mock_ai.return_value = {
                'sql': 'SELECT 1', 'success': True, 'error_msg': '',
                'retry_count': 0, 'execution_time': 0.1,
                'rows': [{'a': 1}], 'columns': [{'name': 'a', 'dtype': 'int'}],
                'chart_type': 'table',
            }
            res = QueryService.execute('ventas totales por mes', csv_mensual.id, test_user)

        mock_ai.assert_called_once()
        assert res['chart_type'] == 'table'

    def test_fallo_de_analisis_se_persiste_como_fallo(self, test_user, csv_mensual):
        with patch('services.analysis.analysis_service.engine.run',
                   side_effect=engine.AnalysisError('sin datos')):
            res = QueryService.execute('segmenta los clientes', csv_mensual.id, test_user)

        registro = QueryHistory.objects.get()
        assert res['success'] is False
        assert registro.success is False
        assert registro.error_msg == 'sin datos'

    def test_segunda_vez_sale_del_cache(self, test_user, csv_mensual):
        pregunta = '¿qué monto se espera los próximos meses?'
        QueryService.execute(pregunta, csv_mensual.id, test_user)
        res = QueryService.execute(pregunta, csv_mensual.id, test_user)

        assert res['cached'] is True
        assert res['chart_type'] == 'forecast'
        assert QueryHistory.objects.count() == 2
