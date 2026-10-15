"""DTOs de entrada/salida para las sesiones de demostración."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DemoSessionInput:
    session_id: str


@dataclass(frozen=True)
class DemoSessionDTO:
    session_id: str
    created_at: datetime
    last_active: datetime
    expires_at: datetime
    expired: bool


@dataclass(frozen=True)
class DemoUserDTO:
    user_id: int
    email: str


@dataclass(frozen=True)
class DemoDatasetDTO:
    dataset_id: int
    name: str
    status: str


@dataclass(frozen=True)
class CleanupSessionResultDTO:
    deleted_dataset_count: int


@dataclass(frozen=True)
class CleanupExpiredResultDTO:
    deleted_session_count: int
    deleted_dataset_count: int
