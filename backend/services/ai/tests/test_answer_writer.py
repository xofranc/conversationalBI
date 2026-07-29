# services/ai/tests/test_answer_writer.py
from unittest.mock import patch

from services.ai.answer_writer import AnswerWriter
from services.ai.suggester import suggest


class TestAnswerWriter:

    def test_narrativa_del_llm_se_limpia_y_retorna(self):
        writer = AnswerWriter.__new__(AnswerWriter)
        writer.llm = _LLMFalso('  Bogotá lidera con\n 215 millones.  ')
        rows = [{'ciudad': 'Bogotá', 'total': 215800000}]

        answer = writer.write('¿ciudad top?', 'SELECT ...', rows, 1)

        assert answer == 'Bogotá lidera con 215 millones.'

    def test_llm_caido_usa_respaldo_determinista(self):
        writer = AnswerWriter.__new__(AnswerWriter)
        writer.llm = _LLMFalso(Exception('ollama caído'))
        rows = [{'ciudad': 'Cali', 'total': 90000000}]

        answer = writer.write('¿ciudad top?', 'SELECT ...', rows, 1)

        assert 'Cali' in answer
        assert '90,000,000' in answer

    def test_respuesta_muy_corta_del_llm_usa_respaldo(self):
        writer = AnswerWriter.__new__(AnswerWriter)
        writer.llm = _LLMFalso('ok')
        rows = [{'total': 5}]

        answer = writer.write('¿total?', 'SELECT ...', rows, 1)

        assert answer != 'ok'
        assert '5' in answer

    def test_sin_filas_no_llama_al_llm(self):
        writer = AnswerWriter.__new__(AnswerWriter)
        writer.llm = _LLMFalso('no debería verse')
        assert writer.write('¿algo?', 'SELECT ...', [], 0) == ''


class _LLMFalso:
    def __init__(self, respuesta):
        self.respuesta = respuesta

    def invoke(self, prompt):
        if isinstance(self.respuesta, Exception):
            raise self.respuesta
        return self.respuesta


class TestSuggester:

    SCHEMA = {
        'tables': [{
            'name': 'main',
            'columns': [
                {'name': 'fecha', 'dtype': 'date'},
                {'name': 'ciudad', 'dtype': 'str'},
                {'name': 'ingresos', 'dtype': 'float'},
            ],
        }]
    }

    def test_sugiere_desde_el_esquema(self):
        sugerencias = suggest(self.SCHEMA)
        assert any('ciudad' in s for s in sugerencias)
        assert any('mensual' in s for s in sugerencias)
        assert len(sugerencias) <= 3

    def test_sin_esquema_no_sugiere(self):
        assert suggest({}) == []
        assert suggest({'tables': []}) == []

    def test_sin_fechas_no_sugiere_evolucion(self):
        schema = {'tables': [{'name': 'main', 'columns': [
            {'name': 'ciudad', 'dtype': 'str'},
        ]}]}
        assert not any('mensual' in s for s in suggest(schema))
