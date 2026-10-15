"""Value objects de consultas compartidos por historial, resultado y feedback."""

from enum import Enum, IntEnum

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
