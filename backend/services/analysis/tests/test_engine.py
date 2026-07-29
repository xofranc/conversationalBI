# services/analysis/tests/test_engine.py
import numpy as np
import pandas as pd
import pytest

from services.analysis import engine


def _serie_mensual(n=24, base=100.0, pendiente=5.0):
    """DataFrame con fechas de fin de mes y una tendencia lineal limpia."""
    fechas = pd.date_range('2023-01-31', periods=n, freq='ME')
    return pd.DataFrame({
        'fecha': fechas,
        'monto': [base + pendiente * i for i in range(n)],
    })


class TestForecast:

    def test_retorna_historia_mas_pronostico(self):
        res = engine.forecast({'main': _serie_mensual()}, 'pronóstico de monto')

        assert res['chart_type'] == 'forecast'
        assert res['chart_config']['xKey'] == 'fecha'
        assert res['chart_config']['yKey'] == 'monto'
        assert res['chart_config']['splitKey'] == 'tipo'

        tipos = [r['tipo'] for r in res['rows']]
        assert tipos.count('real') == 24
        assert tipos.count('pronóstico') == engine.FORECAST_HORIZON
        # historia primero, pronóstico al final
        assert tipos == ['real'] * 24 + ['pronóstico'] * engine.FORECAST_HORIZON

    def test_pronostico_tiene_banda_y_la_historia_no(self):
        res = engine.forecast({'main': _serie_mensual()}, 'pronóstico')
        futuro = [r for r in res['rows'] if r['tipo'] == 'pronóstico']
        historia = [r for r in res['rows'] if r['tipo'] == 'real']

        assert all(r['inferior'] is not None and r['superior'] is not None for r in futuro)
        assert all(r['inferior'] <= r['monto'] <= r['superior'] for r in futuro)
        assert all(r['inferior'] is None for r in historia)

    def test_tendencia_creciente_pronostica_al_alza(self):
        res = engine.forecast({'main': _serie_mensual()}, 'pronóstico')
        ultimo_real = res['rows'][23]['monto']
        ultimo_pronostico = res['rows'][-1]['monto']
        assert ultimo_pronostico > ultimo_real

    def test_pocos_periodos_lanza_error(self):
        with pytest.raises(engine.AnalysisError, match='períodos'):
            engine.forecast({'main': _serie_mensual(n=5)}, 'pronóstico')

    def test_sin_columna_fecha_lanza_error(self):
        df = pd.DataFrame({'a': range(20), 'b': range(20)})
        with pytest.raises(engine.AnalysisError, match='fechas'):
            engine.forecast({'main': df}, 'pronóstico')

    def test_fechas_como_texto_se_parsean(self):
        df = _serie_mensual()
        df['fecha'] = df['fecha'].dt.strftime('%Y-%m-%d')   # CSV real llega así
        res = engine.forecast({'main': df}, 'pronóstico')
        assert res['rows'][0]['fecha'].startswith('2023-01')

    def test_rows_son_json_serializables(self):
        import json
        res = engine.forecast({'main': _serie_mensual()}, 'pronóstico')
        json.dumps(res['rows'])
        json.dumps(res['columns'])


class TestAnomaly:

    def _df_con_outlier(self):
        rng = np.random.RandomState(42)
        normales = pd.DataFrame({
            'monto': rng.normal(100, 5, 30),
            'cantidad': rng.normal(10, 2, 30),
        })
        outlier = pd.DataFrame({'monto': [1000.0], 'cantidad': [10.0]})
        return pd.concat([normales, outlier], ignore_index=True)

    def test_detecta_el_outlier_evidente(self):
        res = engine.anomaly({'main': self._df_con_outlier()}, 'anomalías')

        assert res['chart_type'] == 'anomaly'
        montos = [r['monto'] for r in res['rows']]
        assert 1000.0 in montos
        assert all('score_anomalia' in r for r in res['rows'])

    def test_resultado_ordenado_por_score_descendente(self):
        res = engine.anomaly({'main': self._df_con_outlier()}, 'anomalías')
        scores = [r['score_anomalia'] for r in res['rows']]
        assert scores == sorted(scores, reverse=True)

    def test_una_columna_usa_zscore_robusto(self):
        df = pd.DataFrame({'monto': [10.0] * 15 + [500.0]})
        res = engine.anomaly({'main': df}, 'valores atípicos')
        assert [r['monto'] for r in res['rows']] == [500.0]

    def test_pocas_filas_lanza_error(self):
        df = pd.DataFrame({'monto': [1.0, 2.0, 3.0]})
        with pytest.raises(engine.AnalysisError, match='10 filas'):
            engine.anomaly({'main': df}, 'anomalías')

    def test_sin_numericas_lanza_error(self):
        df = pd.DataFrame({'ciudad': ['Bogotá'] * 15})
        with pytest.raises(engine.AnalysisError, match='numérica'):
            engine.anomaly({'main': df}, 'anomalías')


class TestSegment:

    def _df_dos_grupos(self):
        rng = np.random.RandomState(42)
        a = pd.DataFrame({'x': rng.normal(0, 1, 20), 'y': rng.normal(0, 1, 20)})
        b = pd.DataFrame({'x': rng.normal(10, 1, 20), 'y': rng.normal(10, 1, 20)})
        return pd.concat([a, b], ignore_index=True)

    def test_asigna_segmentos(self):
        res = engine.segment({'main': self._df_dos_grupos()}, 'segmenta los datos')

        assert res['chart_type'] == 'segment'
        assert res['chart_config']['segmentKey'] == 'segmento'
        assert len(res['rows']) == 40

        segmentos = {r['segmento'] for r in res['rows']}
        assert len(segmentos) >= 2
        assert all(s.startswith('Segmento ') for s in segmentos)

    def test_grupos_lejanos_no_comparten_segmento(self):
        res = engine.segment({'main': self._df_dos_grupos()}, 'segmenta')
        cerca = {r['segmento'] for r in res['rows'] if r['x'] < 5}
        lejos = {r['segmento'] for r in res['rows'] if r['x'] >= 5}
        assert cerca.isdisjoint(lejos)

    def test_una_sola_numerica_lanza_error(self):
        df = pd.DataFrame({'monto': range(20), 'ciudad': ['X'] * 20})
        with pytest.raises(engine.AnalysisError, match='dos columnas numéricas'):
            engine.segment({'main': df}, 'segmenta')

    def test_pocas_filas_lanza_error(self):
        df = pd.DataFrame({'x': [1.0, 2.0], 'y': [3.0, 4.0]})
        with pytest.raises(engine.AnalysisError, match='8 filas'):
            engine.segment({'main': df}, 'segmenta')


class TestDrivers:

    def _df_causal(self):
        rng = np.random.RandomState(42)
        x = np.arange(50, dtype=float)
        y = 2 * x + rng.normal(0, 1, 50)
        z = rng.normal(0, 1, 50)                      # independiente
        return pd.DataFrame({'x': x, 'y': y, 'z': z})

    def test_identifica_el_factor_fuerte(self):
        res = engine.drivers({'main': self._df_causal()}, '¿qué factores explican y?')

        assert res['chart_type'] == 'drivers'
        assert res['rows'][0]['factor'] == 'x'
        assert res['rows'][0]['correlacion'] > 0.9
        # el objetivo no aparece como su propio factor
        assert 'y' not in [r['factor'] for r in res['rows']]

    def test_objetivo_mencionado_en_la_pregunta(self):
        res = engine.drivers({'main': self._df_causal()}, '¿qué influye en z?')
        assert 'z' not in [r['factor'] for r in res['rows']]

    def test_orden_por_fuerza_de_correlacion(self):
        res = engine.drivers({'main': self._df_causal()}, 'factores de y')
        fuerzas = [abs(r['correlacion']) for r in res['rows']]
        assert fuerzas == sorted(fuerzas, reverse=True)

    def test_maximo_cinco_factores(self):
        rng = np.random.RandomState(42)
        df = pd.DataFrame({f'c{i}': rng.normal(0, 1, 40) for i in range(8)})
        res = engine.drivers({'main': df}, 'factores de c0')
        assert len(res['rows']) <= 5

    def test_una_sola_numerica_lanza_error(self):
        df = pd.DataFrame({'monto': range(20), 'ciudad': ['X'] * 20})
        with pytest.raises(engine.AnalysisError, match='dos columnas numéricas'):
            engine.drivers({'main': df}, 'factores')


class TestExclusionDeIds:
    """Las columnas identificadoras no son medidas de negocio."""

    def test_id_por_nombre_se_excluye(self):
        df = pd.DataFrame({'id_venta': range(1, 21), 'monto': [float(i) for i in range(20)]})
        df.loc[19, 'monto'] = 9999.0
        res = engine.anomaly({'main': df}, 'anomalías')
        assert res['chart_config']['xKey'] == 'monto'

    def test_id_por_forma_se_excluye(self):
        # enteros únicos monótonos = autoincremental aunque no se llame "id"
        df = pd.DataFrame({'consecutivo': range(1, 21), 'monto': [10.0] * 19 + [900.0]})
        res = engine.anomaly({'main': df}, 'anomalías')
        assert res['chart_config']['xKey'] == 'monto'

    def test_id_no_aparece_como_factor(self):
        rng = np.random.RandomState(42)
        df = pd.DataFrame({
            'id': range(50),
            'x': rng.normal(0, 1, 50),
            'y': rng.normal(0, 1, 50),
        })
        res = engine.drivers({'main': df}, 'factores de y')
        assert 'id' not in [r['factor'] for r in res['rows']]


class TestSummary:

    def test_estadisticos_por_columna(self):
        df = pd.DataFrame({
            'monto': [100.0, 200.0, 300.0, 400.0],
            'ciudad': ['A', 'B', 'C', 'D'],
        })
        res = engine.summary({'main': df}, 'resumen de los datos')

        assert res['chart_type'] == 'table'
        assert len(res['rows']) == 1          # solo la numérica
        fila = res['rows'][0]
        assert fila['columna'] == 'monto'
        assert fila['n'] == 4
        assert fila['media'] == 250.0
        assert fila['mediana'] == 250.0
        assert fila['min'] == 100.0
        assert fila['max'] == 400.0

    def test_ids_quedan_fuera_del_resumen(self):
        df = pd.DataFrame({
            'id_venta': range(1, 11),
            'monto': [float(i * 10) for i in range(10)],
        })
        res = engine.summary({'main': df}, 'describe')
        assert [r['columna'] for r in res['rows']] == ['monto']

    def test_sin_numericas_lanza_error(self):
        df = pd.DataFrame({'ciudad': ['A', 'B']})
        with pytest.raises(engine.AnalysisError, match='columna numérica'):
            engine.summary({'main': df}, 'resumen')

    def test_dispatch_por_intent(self):
        df = pd.DataFrame({'monto': [1.0, 2.0, 3.0]})
        res = engine.run('summary', {'main': df}, 'resumen')
        assert res['chart_type'] == 'table'


class TestDispatcher:

    def test_tipo_desconocido_lanza_error(self):
        with pytest.raises(engine.AnalysisError, match='no soportado'):
            engine.run('magia', {}, 'pregunta')
