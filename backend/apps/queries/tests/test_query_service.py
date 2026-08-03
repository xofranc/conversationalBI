# apps/queries/tests/test_query_service.py
from unittest.mock import patch

import pytest
from rest_framework.exceptions import NotFound, ValidationError

from apps.dataset.models import Dataset
from apps.queries.models import QueryHistory
from apps.queries.services.cache_service import CacheService
from apps.queries.services.query_service import QueryService
from conftest import requires_postgres

pytestmark = pytest.mark.django_db

PREGUNTA = 'ventas totales por region'

@pytest.fixture(autouse=True)
def _ya_materializado(request):
    """Los tests de caché y persistencia no ejercitan archivos:
    la BD del dataset se asume materializada."""
    if request.cls is None or request.cls.__name__ == 'TestMaterializacionPerezosa':
        yield
        return
    with patch('apps.queries.services.query_service.DatabaseService.exists',
               return_value=True):
        yield


class TestGuardsDeDataset:

    def test_dataset_inexistente_lanza_not_found(self, test_user):
        with pytest.raises(NotFound):
            QueryService.execute(PREGUNTA, 99999, test_user)

    def test_dataset_no_ready_lanza_validation_error(self, test_user):
        ds = Dataset.objects.create(
            user=test_user, name='proc', file_path='x.csv',
            status=Dataset.Status.PROCESSING,
        )
        with pytest.raises(ValidationError):
            QueryService.execute(PREGUNTA, ds.id, test_user)


class TestCache:

    def test_hit_no_muta_el_objeto_cacheado(self, test_user, test_dataset):
        version = test_dataset.updated_at.isoformat()
        payload = {'query_id': 1, 'data': [{'a': 1}], 'cached': False}
        CacheService.set(PREGUNTA, test_dataset.id, payload, version)

        result = QueryService.execute(PREGUNTA, test_dataset.id, test_user)

        assert result['cached'] is True
        # El objeto almacenado en caché no fue mutado en sitio
        almacenado = CacheService.get(PREGUNTA, test_dataset.id, version)
        assert almacenado['cached'] is False

    def test_hit_persiste_historial_con_cached_true(self, test_user, test_dataset):
        payload = {'query_id': 99, 'sql': 'SELECT 1', 'data': [], 'model_used': 'm'}
        version = test_dataset.updated_at.isoformat()
        CacheService.set(PREGUNTA, test_dataset.id, payload, version)

        result = QueryService.execute(PREGUNTA, test_dataset.id, test_user)

        registro = QueryHistory.objects.get()
        assert registro.cached is True
        assert result['query_id'] == registro.id   # feedback se ancla al nuevo registro
        assert result['query_id'] != 99            # no al de la consulta original

    def test_dataset_reprocesado_invalida_el_cache(self, test_user, test_dataset):
        payload = {'query_id': 1, 'data': []}
        CacheService.set(PREGUNTA, test_dataset.id, payload, version='version-vieja')

        # updated_at del dataset no coincide con la versión cacheada → miss → llega al guard de AI
        with patch('apps.queries.services.query_service.AIQueryService.execute') as mock_ai:
            mock_ai.return_value = {
                'sql': 'SELECT 1', 'success': False, 'error_msg': 'x',
                'retry_count': 0, 'execution_time': 0.1,
                'rows': [], 'columns': [], 'chart_type': 'table',
            }
            result = QueryService.execute(PREGUNTA, test_dataset.id, test_user)

        assert result['cached'] is False
        mock_ai.assert_called_once()


class TestPersistenciaAtomica:

    @patch('apps.queries.services.query_service.AIQueryService.execute')
    @patch('apps.queries.services.query_service.QueryRepository.save_result')
    def test_si_falla_save_result_no_queda_historial(
        self, mock_save_result, mock_ai, test_user, test_dataset
    ):
        mock_ai.return_value = {
            'sql': 'SELECT 1', 'success': True, 'error_msg': '',
            'retry_count': 0, 'execution_time': 0.1,
            'rows': [{'a': 1}], 'columns': [{'name': 'a', 'dtype': 'int'}],
            'chart_type': 'table',
        }
        mock_save_result.side_effect = Exception('fallo de BD')

        with pytest.raises(Exception):
            QueryService.execute(PREGUNTA, test_dataset.id, test_user)

        # La transacción revirtió el QueryHistory: no queda huérfano con success=True
        assert QueryHistory.objects.count() == 0


class TestMaterializacionPerezosa:
    """Datasets anteriores a la materialización se convierten en la
    primera consulta, una sola vez."""

    @requires_postgres
    def test_dataset_sin_bd_se_materializa_al_consultar(
        self, test_user, tmp_path, settings, schema_cleanup
    ):
        settings.MEDIA_ROOT = str(tmp_path)
        import pandas as pd
        pd.DataFrame({'a': [1, 2, 3]}).to_csv(tmp_path / 'viejo.csv', index=False)
        ds = Dataset.objects.create(
            user=test_user, name='viejo', file_path='viejo.csv',
            status=Dataset.Status.READY,
        )

        with patch('apps.queries.services.query_service.AIQueryService.execute') as mock_ai:
            mock_ai.return_value = {
                'sql': 'SELECT 1', 'success': False, 'error_msg': 'x',
                'retry_count': 0, 'execution_time': 0.1,
                'rows': [], 'columns': [], 'chart_type': 'table',
            }
            QueryService.execute(PREGUNTA, ds.id, test_user)

        ds.refresh_from_db()
        assert ds.db_path == f'ds_{ds.id}'
        schema_cleanup.append(ds.db_path)

        # Segunda consulta: ya materializado, no se vuelve a convertir
        with patch('apps.queries.services.query_service.DatabaseService.materialize') as mock_mat:
            with patch('apps.queries.services.query_service.AIQueryService.execute') as mock_ai:
                mock_ai.return_value = {
                    'sql': 'SELECT 1', 'success': False, 'error_msg': 'x',
                    'retry_count': 0, 'execution_time': 0.1,
                    'rows': [], 'columns': [], 'chart_type': 'table',
                }
                QueryService.execute(PREGUNTA, ds.id, test_user)
        mock_mat.assert_not_called()


class TestContextoDeConversacion:

    def test_solo_exitosas_no_cacheadas_y_no_analisis(self, test_user, test_dataset):
        from apps.queries.models import QueryHistory as QH
        crear = lambda **kw: QH.objects.create(user=test_user, dataset=test_dataset, **kw)
        crear(question='q1', sql_generated='SELECT 1', success=True)
        crear(question='q2', sql_generated='SELECT 2', success=True)
        crear(question='fallida', sql_generated='SELECT x', success=False)
        crear(question='cacheada', sql_generated='SELECT 3', success=True, cached=True)
        crear(question='analisis', sql_generated='-- método', success=True)

        ctx = QueryService._conversation_context(test_user, test_dataset.id)

        preguntas = [c['question'] for c in ctx]
        assert preguntas == ['q1', 'q2']          # orden vieja → nueva

    def test_limite_de_contexto(self, test_user, test_dataset):
        from apps.queries.models import QueryHistory as QH
        for i in range(6):
            QH.objects.create(
                user=test_user, dataset=test_dataset,
                question=f'q{i}', sql_generated=f'SELECT {i}', success=True,
            )
        ctx = QueryService._conversation_context(test_user, test_dataset.id)
        assert len(ctx) == 3                       # HISTORY_CONTEXT
        assert ctx[-1]['question'] == 'q5'         # la más reciente al final
