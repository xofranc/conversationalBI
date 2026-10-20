"""Contratos de persistencia para el dominio de usuarios."""

from __future__ import annotations

from typing import Protocol

from .entities import Profile, User
from .value_objects import EmailAddress, PhoneNumber


class UserRepository(Protocol):
    def get_by_id(self, user_id: int) -> User | None: ...

    def get_by_email(self, email: EmailAddress) -> User | None: ...

    def save(self, user: User) -> User: ...


class ProfileRepository(Protocol):
    """Profile tiene cardinalidad uno-a-uno con User y teléfono único cuando existe."""

    def get_by_user_id(self, user_id: int) -> Profile | None: ...

    def phone_number_exists(self, phone_number: PhoneNumber, *, excluding_profile_id: int | None = None) -> bool: ...

    def save(self, profile: Profile) -> Profile: ...

    def increment_query_count(self, user_id: int) -> None: ...
