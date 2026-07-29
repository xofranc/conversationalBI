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


class TestContextoDeConversacion:

    def test_sin_historia_no_hay_seccion(self):
        prompt = PromptBuilder.build('ventas por región', SCHEMA)
        assert 'CONVERSACIÓN PREVIA (tema de la charla' not in prompt

    def test_historia_aparece_en_el_prompt(self):
        historia = [
            {'question': 'ventas por ciudad', 'sql': 'SELECT ciudad, SUM(x) FROM main GROUP BY ciudad'},
            {'question': 'y las del año pasado?', 'sql': 'SELECT ... WHERE ...'},
        ]
        prompt = PromptBuilder.build('ahora por mes', SCHEMA, historia)
        assert 'CONVERSACIÓN PREVIA (tema de la charla' in prompt
        assert 'ventas por ciudad' in prompt
        assert 'y las del año pasado?' in prompt


class TestValoresDeColumna:

    def test_info_de_columna_aparece_en_el_prompt(self):
        schema = {'tables': [{
            'name': 'main', 'row_count': 10,
            'columns': [
                {'name': 'ciudad', 'dtype': 'str', 'info': 'valores: Bogotá, Cali'},
                {'name': 'fecha', 'dtype': 'date', 'info': 'rango: 2024-01-01 → 2024-12-31'},
            ],
        }]}
        prompt = PromptBuilder.build('algo', schema)
        assert 'valores: Bogotá, Cali' in prompt
        assert 'rango: 2024-01-01 → 2024-12-31' in prompt


class TestPromptDeRespuesta:

    def test_incluye_pregunta_filas_y_conteo(self):
        prompt = PromptBuilder.build_answer(
            'ventas por ciudad', 'SELECT ...',
            [{'ciudad': 'Bogotá', 'total': 100}], 1,
        )
        assert 'ventas por ciudad' in prompt
        assert 'Bogotá' in prompt
        assert '(1 filas)' in prompt

    def test_filas_se_truncan(self):
        rows = [{'a': i} for i in range(40)]
        prompt = PromptBuilder.build_answer('q', 'sql', rows, 40)
        assert 'filas más' in prompt
