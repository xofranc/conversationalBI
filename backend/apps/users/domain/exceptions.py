"""Excepciones propias del dominio de usuarios."""


class DomainError(Exception):
    """Base para errores de negocio de esta app."""


class InvalidPhoneNumber(DomainError, ValueError):
    """El teléfono no cumple el formato persistido por Profile."""


class InvalidEmailAddress(DomainError, ValueError):
    """La dirección requerida está vacía."""
