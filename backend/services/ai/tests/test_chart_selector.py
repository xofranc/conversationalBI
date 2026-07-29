# services/ai/tests/test_chart_selector.py
from services.ai.chart_selector import ChartSelector


def _cols(*cols):
    return [{'name': name, 'dtype': dtype} for name, dtype in cols]


class TestChartSelectorSelect:
    """select() entrega chart_config listo para el frontend."""

    def test_fecha_y_numero_es_linea_con_claves(self):
        columns = _cols(('mes', 'date'), ('total', 'float'))
        rows = [{'mes': '2024-01', 'total': 10}, {'mes': '2024-02', 'total': 12}]

        sel = ChartSelector.select(columns, rows)

        assert sel['chart_type'] == 'line'
        assert sel['chart_config'] == {'xKey': 'mes', 'yKey': 'total'}

    def test_categoria_y_numero_pocas_filas_es_torta(self):
        columns = _cols(('ciudad', 'str'), ('ventas', 'float'))
        rows = [{'ciudad': c, 'ventas': v} for c, v in
                [('Bogotá', 1), ('Cali', 2), ('Medellín', 3)]]

        sel = ChartSelector.select(columns, rows)

        assert sel['chart_type'] == 'pie'
        assert sel['chart_config']['nameKey'] == 'ciudad'
        assert sel['chart_config']['valueKey'] == 'ventas'

    def test_categoria_y_numero_muchas_filas_es_barras(self):
        columns = _cols(('ciudad', 'str'), ('ventas', 'float'))
        rows = [{'ciudad': f'c{i}', 'ventas': i} for i in range(10)]

        sel = ChartSelector.select(columns, rows)

        assert sel['chart_type'] == 'bar'
        assert sel['chart_config']['xKey'] == 'ciudad'
        assert sel['chart_config']['yKey'] == 'ventas'

    def test_dos_numeros_es_dispersion(self):
        columns = _cols(('precio', 'float'), ('cantidad', 'int'))
        rows = [{'precio': 1.0, 'cantidad': 2}]

        sel = ChartSelector.select(columns, rows)

        assert sel['chart_type'] == 'scatter'
        assert sel['chart_config'] == {'xKey': 'precio', 'yKey': 'cantidad'}

    def test_sin_datos_es_tabla(self):
        assert ChartSelector.select([], [])['chart_type'] == 'table'
        assert ChartSelector.select(_cols(('a', 'str')), [])['chart_type'] == 'table'

    def test_pick_sigue_devolviendo_solo_el_tipo(self):
        columns = _cols(('mes', 'date'), ('total', 'float'))
        rows = [{'mes': '2024-01', 'total': 10}]
        assert ChartSelector.pick(columns, rows) == 'line'
