"""Excepciones propias del dominio core."""


class DomainError(Exception):
    """Base para errores de negocio de esta app."""


class InvalidSessionIdentifier(DomainError, ValueError):
    """El identificador no cumple los límites del campo persistido."""
