# services/analysis/intent.py
"""
Detección determinística de intención analítica (sin LLM).

Palabras clave en español sobre la pregunta normalizada. Si ninguna
coincide, la pregunta sigue el camino normal (SQL generado por el LLM).
"""

from apps.queries.domain.policies import AnalysisIntent, AnalysisIntentPolicy

FORECAST = AnalysisIntent.FORECAST.value
ANOMALY = AnalysisIntent.ANOMALY.value
SEGMENT = AnalysisIntent.SEGMENT.value
DRIVERS = AnalysisIntent.DRIVERS.value
SUMMARY = AnalysisIntent.SUMMARY.value

_KEYWORDS = AnalysisIntentPolicy._KEYWORDS


def detect(question: str):
    """
    Retorna el tipo de análisis pedido ('forecast' | 'anomaly' | 'segment'
    | 'drivers') o None si la pregunta es una consulta SQL normal.
    """
    intent = AnalysisIntentPolicy.detect(question)
    return intent.value if intent is not None else None
