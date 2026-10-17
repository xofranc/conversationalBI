"""Entidades puras de usuarios y perfiles."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date

from .value_objects import EmailAddress, PhoneNumber, UserType


@dataclass(frozen=True)
class User:
    email: EmailAddress
    first_name: str
    last_name: str
    is_active: bool = True
    user_type: UserType = UserType.USER
    id: int | None = None

    @property
    def user_type_numeric(self) -> int:
        return {UserType.USER: 1, UserType.ADMIN: 2}.get(self.user_type, 0)


@dataclass(frozen=True)
class Profile:
    """Perfil uno-a-uno con User; el incremento devuelve una copia inmutable."""

    user_id: int
    bio: str = ""
    phone_number: PhoneNumber | None = None
    birth_date: date | None = None
    entry_date: date | None = None
    query_count: int = 0
    query_limit: int = 100
    id: int | None = None

    @property
    def can_query(self) -> bool:
        """Disponibilidad informativa de cuota; no implica enforcement en el flujo actual."""
        return self.query_count < self.query_limit

    def increment_query_count(self) -> "Profile":
        return replace(self, query_count=self.query_count + 1)
