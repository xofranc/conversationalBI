"""Contrato de persistencia para las sesiones demo."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, Sequence

from .entities import DemoSession
from .value_objects import SessionIdentifier


class DemoSessionRepository(Protocol):
    """La sesión tiene identificador único; expiración se calcula en dominio."""

    def get_by_session_id(self, session_id: SessionIdentifier) -> DemoSession | None: ...

    def save(self, session: DemoSession) -> DemoSession: ...

    def list_expired_before(self, cutoff: datetime) -> Sequence[DemoSession]: ...

    def delete(self, session_id: SessionIdentifier) -> None: ...
