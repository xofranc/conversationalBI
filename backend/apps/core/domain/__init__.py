"""Dominio de sesiones anónimas de demostración."""

from .entities import DemoSession, DEMO_SESSION_TTL
from .exceptions import DomainError, InvalidSessionIdentifier
from .value_objects import SessionIdentifier

__all__ = [
    "DEMO_SESSION_TTL",
    "DemoSession",
    "DomainError",
    "InvalidSessionIdentifier",
    "SessionIdentifier",
]
