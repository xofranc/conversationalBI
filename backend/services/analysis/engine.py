"""Fachada legacy del motor estadístico implementado en queries.infrastructure."""

from apps.dataset.infrastructure.schema_service import SchemaService
from apps.queries.domain.policies import AnalysisLimits
from apps.queries.infrastructure.analysis import engine as _engine
from . import intent

AnalysisError = _engine.AnalysisError
_LIMITS = AnalysisLimits()

# Constantes públicas legacy: su origen canónico es la política de dominio.
MAX_HISTORY_PERIODS = _LIMITS.max_history_periods
MAX_ANOMALIES = _LIMITS.max_anomalies
MAX_SEGMENT_ROWS = _LIMITS.max_segment_rows
FORECAST_HORIZON = _LIMITS.forecast_horizon
MIN_FORECAST_PERIODS = _LIMITS.min_forecast_periods

_infer_dtype = SchemaService.infer_dtype


def forecast(tables: dict, question: str) -> dict:
    return _engine.forecast(tables, question, _infer_dtype, _LIMITS)


def anomaly(tables: dict, question: str) -> dict:
    return _engine.anomaly(tables, question, _infer_dtype, _LIMITS)


def segment(tables: dict, question: str) -> dict:
    return _engine.segment(tables, question, _infer_dtype, _LIMITS)


def drivers(tables: dict, question: str) -> dict:
    return _engine.drivers(tables, question, _infer_dtype, _LIMITS)


def summary(tables: dict, question: str) -> dict:
    return _engine.summary(tables, question, _infer_dtype, _LIMITS)


def run(analysis_type: str, tables: dict, question: str) -> dict:
    return _engine.run(
        analysis_type,
        tables,
        question,
        infer_dtype=_infer_dtype,
        limits=_LIMITS,
    )
