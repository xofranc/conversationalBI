"""DTOs de entrada y salida para los casos de uso de usuarios."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class GetProfileInput:
    user_id: int


@dataclass(frozen=True)
class UpdateProfileInput:
    user_id: int
    bio: str | None = None
    phone_number: str | None = None
    birth_date: date | None = None
    update_bio: bool = False
    update_phone_number: bool = False
    update_birth_date: bool = False


@dataclass(frozen=True)
class ProfileDTO:
    user_id: int
    bio: str
    phone_number: str | None
    birth_date: date | None
    entry_date: date | None


@dataclass(frozen=True)
class GetQuotaInput:
    user_id: int


@dataclass(frozen=True)
class QuotaDTO:
    query_count: int
    query_limit: int
    available: bool


@dataclass(frozen=True)
class CanAccessDatasetInput:
    user_id: int
    dataset_id: int


@dataclass(frozen=True)
class AccessDecisionDTO:
    allowed: bool


@dataclass(frozen=True)
class AuthenticateInput:
    credential: str


@dataclass(frozen=True)
class AuthenticatedIdentityDTO:
    user_id: int
    email: str
