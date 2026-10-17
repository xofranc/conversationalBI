"""Dominio de sesiones anónimas de demostración."""

from .entities import DemoSession, DEMO_SESSION_TTL
from .exceptions import DomainError, InvalidSessionIdentifier
from .ports import DemoDatasetLifecycle
from .value_objects import DemoDatasetDTO, SessionIdentifier

__all__ = [
    "DEMO_SESSION_TTL",
    "DemoDatasetDTO",
    "DemoDatasetLifecycle",
    "DemoSession",
    "DomainError",
    "InvalidSessionIdentifier",
    "SessionIdentifier",
]
