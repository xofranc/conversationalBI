"""Excepciones propias del dominio de consultas."""


class DomainError(Exception):
    """Base para errores de negocio de esta app."""


class InvalidFeedbackScore(DomainError, ValueError):
    """El score no es uno de los valores persistidos permitidos."""


class InvalidPolicyConfiguration(DomainError, ValueError):
    """Una policy de dominio recibió límites incoherentes o inválidos."""


class SQLSafetyViolation(DomainError):
    """Rechazo de seguridad SQL que no debe reintentarse."""

    retryable = False


class UnsupportedStatisticalAnalysis(DomainError):
    """El conjunto de datos no soporta el análisis estadístico solicitado."""
