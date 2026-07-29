# services/analysis/tests/test_intent.py
from services.analysis import intent


class TestDeteccionDeIntencion:

    def test_pronostico(self):
        assert intent.detect('¿cuál es el pronóstico de ventas para diciembre?') == 'forecast'
        assert intent.detect('¿qué ingresos se esperan los próximos meses?') == 'forecast'
        assert intent.detect('haz una proyección del monto') == 'forecast'

    def test_anomalias(self):
        assert intent.detect('¿hay anomalías en los montos?') == 'anomaly'
        assert intent.detect('muéstrame los valores atípicos') == 'anomaly'
        assert intent.detect('¿algún outlier en precios?') == 'anomaly'

    def test_segmentacion(self):
        assert intent.detect('segmenta los clientes por monto y frecuencia') == 'segment'
        assert intent.detect('¿qué clusters hay en los datos?') == 'segment'

    def test_factores(self):
        assert intent.detect('¿qué factores explican el monto?') == 'drivers'
        assert intent.detect('¿qué influye en el precio?') == 'drivers'
        assert intent.detect('¿qué variables se correlacionan con ingresos?') == 'drivers'

    def test_resumen(self):
        assert intent.detect('dame un resumen de los datos') == 'summary'
        assert intent.detect('describe el dataset') == 'summary'
        assert intent.detect('¿cuáles son las estadísticas de las columnas?') == 'summary'

    def test_consulta_sql_normal_no_es_analisis(self):
        assert intent.detect('ventas totales por ciudad') is None
        assert intent.detect('top 5 productos por ingresos') is None
        assert intent.detect('promedio de ventas por mes') is None

    def test_no_distingue_mayusculas(self):
        assert intent.detect('¿HAY ANOMALÍAS?') == 'anomaly'
