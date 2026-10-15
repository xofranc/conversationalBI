"""Casos de uso de sesiones demo, usuarios temporales y expiración."""

from __future__ import annotations

from datetime import datetime

from apps.core.domain.entities import DEMO_SESSION_TTL, DemoSession
from apps.core.domain.repositories import DemoSessionRepository
from apps.core.domain.value_objects import SessionIdentifier
from apps.users.domain.entities import User
from apps.users.domain.repositories import UserRepository
from apps.users.domain.value_objects import EmailAddress

from .dtos import (
    CleanupExpiredResultDTO,
    CleanupSessionResultDTO,
    DemoDatasetDTO,
    DemoSessionDTO,
    DemoSessionInput,
    DemoUserDTO,
)
from .ports import Clock, DemoDatasetLifecycle


def _session_dto(session: DemoSession, now: datetime) -> DemoSessionDTO:
    return DemoSessionDTO(
        session_id=str(session.session_id),
        created_at=session.created_at,
        last_active=session.last_active,
        expires_at=session.expires_at,
        expired=session.is_expired(now),
    )


class GetOrCreateDemoSession:
    """Obtiene una sesión existente o crea una con timestamps del reloj."""

    def __init__(self, sessions: DemoSessionRepository, clock: Clock) -> None:
        self._sessions = sessions
        self._clock = clock

    def execute(self, request: DemoSessionInput) -> DemoSessionDTO:
        identifier = SessionIdentifier(request.session_id)
        session = self._sessions.get_by_session_id(identifier)
        if session is None:
            now = self._clock.now()
            session = self._sessions.save(DemoSession(
                session_id=identifier,
                created_at=now,
                last_active=now,
            ))
        return _session_dto(session, self._clock.now())


class GetOrCreateDemoUser:
    """Provisiona la identidad estable asociada a una sesión demo."""

    def __init__(self, users: UserRepository) -> None:
        self._users = users

    def execute(self, request: DemoSessionInput) -> DemoUserDTO:
        identifier = SessionIdentifier(request.session_id)
        email = EmailAddress(f"demo_{identifier.value}@demo.local")
        user = self._users.get_by_email(email)
        if user is None:
            user = self._users.save(User(
                email=email,
                first_name="Demo",
                last_name="User",
                is_active=True,
            ))
        if user.id is None:
            raise RuntimeError("El repositorio debe asignar identidad al usuario demo")
        return DemoUserDTO(user_id=user.id, email=str(user.email))


class ListDemoSessionDatasets:
    """Lista los datasets pertenecientes al usuario demo de la sesión."""

    def __init__(self, get_demo_user: GetOrCreateDemoUser, datasets: DemoDatasetLifecycle) -> None:
        self._get_demo_user = get_demo_user
        self._datasets = datasets

    def execute(self, request: DemoSessionInput) -> tuple[DemoDatasetDTO, ...]:
        user = self._get_demo_user.execute(request)
        return tuple(self._datasets.list_for_user(user.user_id))


class CleanupDemoSession:
    """Intenta eliminar todos los datasets de una sesión sin abortar por uno."""

    def __init__(self, get_demo_user: GetOrCreateDemoUser, datasets: DemoDatasetLifecycle) -> None:
        self._get_demo_user = get_demo_user
        self._datasets = datasets

    def execute(self, request: DemoSessionInput) -> CleanupSessionResultDTO:
        user = self._get_demo_user.execute(request)
        dataset_ids = tuple(self._datasets.list_ids_for_user(user.user_id))
        for dataset_id in dataset_ids:
            try:
                self._datasets.delete(dataset_id, user.user_id)
            except Exception:
                # La limpieza de recursos externos es best-effort por dataset.
                continue
        return CleanupSessionResultDTO(deleted_dataset_count=len(dataset_ids))


class CleanupExpiredDemoSessions:
    """Limpia datasets y elimina sesiones inactivas más allá del TTL."""

    def __init__(
        self,
        sessions: DemoSessionRepository,
        cleanup_session: CleanupDemoSession,
        clock: Clock,
    ) -> None:
        self._sessions = sessions
        self._cleanup_session = cleanup_session
        self._clock = clock

    def execute(self) -> CleanupExpiredResultDTO:
        now = self._clock.now()
        cutoff = now - DEMO_SESSION_TTL
        expired = self._sessions.list_expired_before(cutoff)
        deleted_datasets = 0
        deleted_sessions = 0
        for session in expired:
            outcome = self._cleanup_session.execute(DemoSessionInput(str(session.session_id)))
            deleted_datasets += outcome.deleted_dataset_count
            self._sessions.delete(session.session_id)
            deleted_sessions += 1
        return CleanupExpiredResultDTO(
            deleted_session_count=deleted_sessions,
            deleted_dataset_count=deleted_datasets,
        )
