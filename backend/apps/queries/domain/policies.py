"""Políticas de negocio deterministas de consulta y análisis.

No contiene generación de prompts, parsing/validación sintáctica de SQL,
ejecución de SQL, codecs ni algoritmos que dependan de pandas/ML.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .exceptions import InvalidPolicyConfiguration


def _require_positive_integer(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise InvalidPolicyConfiguration(f"{field_name} debe ser un entero positivo")


class AnalysisIntent(str, Enum):
    FORECAST = "forecast"
    ANOMALY = "anomaly"
    SEGMENT = "segment"
    DRIVERS = "drivers"
    SUMMARY = "summary"


class AnalysisIntentPolicy:
    """Clasificador por subcadenas; conserva orden y keywords actuales."""

    _KEYWORDS = {
        AnalysisIntent.FORECAST: (
            "pronóstico", "pronostico", "predecir", "predicción", "prediccion",
            "proyección", "proyeccion", "proyectar", "forecast", "futuro", "futura",
            "próximos", "proximos", "próximas", "proximas", "va a seguir",
            "seguirá", "seguira", "espera para",
        ),
        AnalysisIntent.ANOMALY: (
            "anomalía", "anomalia", "anomalías", "anomalias", "atípico", "atipico",
            "atípicos", "atipicos", "atípica", "atipica", "outlier", "outliers",
            "inusual", "inusuales", "extraño", "extrano", "extraños", "extranos",
            "fuera de lo normal", "se salen",
        ),
        AnalysisIntent.SEGMENT: (
            "segmento", "segmentos", "segmentar", "segmenta", "segmente",
            "segmentación", "segmentacion", "cluster", "clusters", "agrupar",
            "agrupación", "agrupacion", "grupos de", "perfiles de",
        ),
        AnalysisIntent.DRIVERS: (
            "factores", "drivers", "qué influye", "que influye", "qué afecta",
            "que afecta", "qué explica", "que explica", "correlación", "correlacion",
            "correlacionado", "relaciona", "relacionadas", "impacta", "determina",
            "mueve", "detrás de", "detras de",
        ),
        AnalysisIntent.SUMMARY: (
            "resumen", "resúmenes", "describe", "describir", "descripción",
            "descripcion", "estadísticas", "estadisticas", "estadístico",
            "estadistico", "panorama", "visión general", "vision general",
            "vista general", "overview",
        ),
    }

    @classmethod
    def detect(cls, question: str) -> AnalysisIntent | None:
        normalized = question.lower()
        for intent, keywords in cls._KEYWORDS.items():
            if any(keyword in normalized for keyword in keywords):
                return intent
        return None


@dataclass(frozen=True)
class AnalysisLimits:
    """Límites deterministas de análisis, expuestos como atributos de solo lectura.

    Aplicación e infraestructura deben leer estos valores en vez de mantener
    copias locales de los mismos límites.
    """

    max_history_periods: int = 100
    max_anomalies: int = 20
    max_segment_rows: int = 300
    forecast_horizon: int = 6
    min_forecast_periods: int = 8
    min_anomaly_rows: int = 10
    min_segment_rows: int = 8

    def __post_init__(self) -> None:
        for field_name in (
            "max_history_periods",
            "max_anomalies",
            "max_segment_rows",
            "forecast_horizon",
            "min_forecast_periods",
            "min_anomaly_rows",
            "min_segment_rows",
        ):
            _require_positive_integer(getattr(self, field_name), field_name)

        if self.min_forecast_periods > self.max_history_periods:
            raise InvalidPolicyConfiguration(
                "min_forecast_periods no puede superar max_history_periods"
            )


@dataclass(frozen=True)
class QueryExecutionPolicy:
    """Límites inmutables de reintentos y filas por ejecución.

    La orquestación de reintentos y el recorte del resultado siguen fuera del
    dominio; los motores leen aquí sus valores canónicos.
    """

    max_attempts: int = 3
    max_result_rows: int = 1000

    def __post_init__(self) -> None:
        _require_positive_integer(self.max_attempts, "max_attempts")
        _require_positive_integer(self.max_result_rows, "max_result_rows")


@dataclass(frozen=True)
class SQLSafetyPolicy:
    """Declaración canónica de seguridad SQL para consumir desde capas externas.

    ``forbidden_operations`` es la lista de operaciones que debe aplicar el
    validador; tokenización, parsing y aplicación de estas reglas no pertenecen
    al dominio.
    """

    allowed_statement: str = "SELECT"
    forbidden_operations: tuple[str, ...] = (
        "UNION", "ATTACH", "DETACH", "PRAGMA", "LOAD_EXTENSION", "CREATE",
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "REPLACE",
    )
    allows_single_terminal_semicolon: bool = True
    security_rejection_is_retryable: bool = False
