# services/ai/tests/test_prompt_builder.py
from services.ai.prompt_builder import PromptBuilder

SCHEMA = {
    'tables': [{
        'name': 'ventas',
        'columns': [
            {'name': 'region', 'dtype': 'str', 'sample': ['Bogota', 'Cali']},
            {'name': 'monto', 'dtype': 'float', 'sample': [100.5, 200.0]},
        ],
    }]
}


class TestBuild:

    def test_incluye_pregunta_y_schema(self):
        prompt = PromptBuilder.build('ventas por region', SCHEMA)
        assert 'ventas por region' in prompt
        assert 'ventas' in prompt
        assert 'monto (float)' in prompt


class TestBuildCorrection:

    def test_incluye_la_pregunta_original(self):
        prompt = PromptBuilder.build_correction(
            question='ventas por mes',
            schema=SCHEMA,
            previous_sql='SELECT * FROM ventas',
            error='no such column: mes',
        )
        assert 'ventas por mes' in prompt
        assert 'SELECT * FROM ventas' in prompt
        assert 'no such column: mes' in prompt
