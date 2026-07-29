# services/ai/tests/test_ai_query_service.py
from unittest.mock import patch

import pytest

from services.ai.ai_query_service import AIQueryService

SCHEMA = {'tables': [{'name': 'main', 'columns': []}]}


@pytest.fixture
def mocks():
    with patch('services.ai.ai_query_service.SQLAgent') as mock_agent_cls, \
         patch('services.ai.ai_query_service.AnswerWriter') as mock_writer_cls, \
         patch('services.ai.ai_query_service.SQLExecutor') as mock_executor:
        mock_writer_cls.return_value.write.return_value = 'respuesta de prueba'
        yield mock_agent_cls.return_value, mock_executor


class TestFailFastSeguridad:

    def test_sql_peligroso_no_reintenta(self, mocks):
        agent, executor = mocks
        agent.run.return_value = 'DROP TABLE main'

        result = AIQueryService.execute('borra todo', 1, SCHEMA)

        assert result['success'] is False
        assert agent.run.call_count == 1          # fail-fast: sin reintentos
        executor.run.assert_not_called()          # jamás llega al sandbox

    def test_no_sql_possible_no_reintenta(self, mocks):
        agent, executor = mocks
        agent.run.return_value = 'NO_SQL_POSSIBLE'

        result = AIQueryService.execute('pregunta imposible', 1, SCHEMA)

        assert result['success'] is False
        assert agent.run.call_count == 1


class TestFlujoExitoso:

    def test_consulta_valida_retorna_filas(self, mocks):
        agent, executor = mocks
        agent.run.return_value = 'SELECT ciudad FROM main'
        executor.run.return_value = (
            [{'ciudad': 'Bogota'}],
            [{'name': 'ciudad', 'dtype': 'str'}],
        )

        result = AIQueryService.execute('lista las ciudades', 1, SCHEMA)

        assert result['success'] is True
        assert result['rows'] == [{'ciudad': 'Bogota'}]
        assert result['retry_count'] == 0

    def test_error_de_ejecucion_reintenta_con_correccion(self, mocks):
        agent, executor = mocks
        agent.run.side_effect = ['SELECT mal', 'SELECT ciudad FROM main']
        executor.run.side_effect = [
            Exception('no such column: mal'),
            ([{'ciudad': 'Cali'}], [{'name': 'ciudad', 'dtype': 'str'}]),
        ]

        result = AIQueryService.execute('lista las ciudades', 1, SCHEMA)

        assert result['success'] is True
        assert agent.run.call_count == 2
        assert result['retry_count'] == 1
        # El segundo prompt fue de corrección e incluye la pregunta original
        prompt_correccion = agent.run.call_args_list[1][0][0]
        assert 'lista las ciudades' in prompt_correccion
