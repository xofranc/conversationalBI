# services/analysis/intent.py
"""
Detección determinística de intención analítica (sin LLM).

Palabras clave en español sobre la pregunta normalizada. Si ninguna
coincide, la pregunta sigue el camino normal (SQL generado por el LLM).
"""

FORECAST = 'forecast'
ANOMALY = 'anomaly'
SEGMENT = 'segment'
DRIVERS = 'drivers'
SUMMARY = 'summary'

_KEYWORDS = {
    FORECAST: (
        'pronóstico', 'pronostico', 'predecir', 'predicción', 'prediccion',
        'proyección', 'proyeccion', 'proyectar', 'forecast', 'futuro', 'futura',
        'próximos', 'proximos', 'próximas', 'proximas', 'va a seguir',
        'seguirá', 'seguira', 'espera para',
    ),
    ANOMALY: (
        'anomalía', 'anomalia', 'anomalías', 'anomalias', 'atípico', 'atipico',
        'atípicos', 'atipicos', 'atípica', 'atipica', 'outlier', 'outliers',
        'inusual', 'inusuales', 'extraño', 'extrano', 'extraños', 'extranos',
        'fuera de lo normal', 'se salen',
    ),
    SEGMENT: (
        'segmento', 'segmentos', 'segmentar', 'segmenta', 'segmente',
        'segmentación', 'segmentacion', 'cluster', 'clusters', 'agrupar',
        'agrupación', 'agrupacion', 'grupos de', 'perfiles de',
    ),
    DRIVERS: (
        'factores', 'drivers', 'qué influye', 'que influye', 'qué afecta',
        'que afecta', 'qué explica', 'que explica', 'correlación', 'correlacion',
        'correlacionado', 'relaciona', 'relacionadas', 'impacta', 'determina',
        'mueve', 'detrás de', 'detras de',
    ),
    SUMMARY: (
        'resumen', 'resúmenes', 'describe', 'describir', 'descripción',
        'descripcion', 'estadísticas', 'estadisticas', 'estadístico',
        'estadistico', 'panorama', 'visión general', 'vision general',
        'vista general', 'overview',
    ),
}


def detect(question: str):
    """
    Retorna el tipo de análisis pedido ('forecast' | 'anomaly' | 'segment'
    | 'drivers') o None si la pregunta es una consulta SQL normal.
    """
    q = question.lower()
    for analysis_type, keywords in _KEYWORDS.items():
        if any(keyword in q for keyword in keywords):
            return analysis_type
    return None
