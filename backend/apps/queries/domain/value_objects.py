"""Value objects de consultas compartidos por historial, resultado y feedback."""

from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Any

from .exceptions import InvalidFeedbackScore


class ChartType(str, Enum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    TABLE = "table"
    FORECAST = "forecast"
    ANOMALY = "anomaly"
    SEGMENT = "segment"
    DRIVERS = "drivers"


class FeedbackScore(IntEnum):
    USEFUL = 1
    NOT_USEFUL = -1

    @classmethod
    def from_value(cls, value: int) -> "FeedbackScore":
        try:
            return cls(value)
        except ValueError as error:
            raise InvalidFeedbackScore("El feedback debe ser útil (1) o no útil (-1)") from error


@dataclass(frozen=True)
class ChartSelection:
    """Tipo y configuración visual elegidos para un resultado."""

    chart_type: str
    chart_config: dict[str, Any]


@dataclass(frozen=True)
class SQLExecutionResult:
    """Filas y columnas producidas por la ejecución de una consulta SQL."""

    rows: tuple[dict[str, Any], ...]
    columns: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class StatisticalCalculationResult:
    """Resultado de cálculo estadístico, independiente de librerías técnicas."""

    rows: tuple[dict[str, Any], ...]
    columns: tuple[dict[str, Any], ...]
    chart_type: str
    chart_config: dict[str, Any]
    method: str
