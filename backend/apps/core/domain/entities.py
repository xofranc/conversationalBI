"""Entidad y regla de expiración de sesiones demo."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .value_objects import SessionIdentifier


DEMO_SESSION_TTL = timedelta(hours=24)


@dataclass(frozen=True)
class DemoSession:
    session_id: SessionIdentifier
    created_at: datetime
    last_active: datetime

    @property
    def expires_at(self) -> datetime:
        return self.last_active + DEMO_SESSION_TTL

    def is_expired(self, at: datetime) -> bool:
        """Expira solo cuando transcurrieron estrictamente más de 24 horas inactiva."""
        return at - self.last_active > DEMO_SESSION_TTL
