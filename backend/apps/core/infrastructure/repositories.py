"""Repositorio ORM de sesiones demo."""

from __future__ import annotations

from datetime import datetime

from apps.core.domain.entities import DemoSession as SessionEntity
from apps.core.domain.repositories import DemoSessionRepository
from apps.core.domain.value_objects import SessionIdentifier

from .models import DemoSession as SessionModel


def _session_entity(model: SessionModel) -> SessionEntity:
    return SessionEntity(
        session_id=SessionIdentifier(model.session_id),
        created_at=model.created_at,
        last_active=model.last_active,
    )


class DjangoDemoSessionRepository(DemoSessionRepository):
    def get_by_session_id(self, session_id: SessionIdentifier) -> SessionEntity | None:
        model = SessionModel.objects.filter(session_id=session_id.value).first()
        return _session_entity(model) if model is not None else None

    def save(self, session: SessionEntity) -> SessionEntity:
        model, _ = SessionModel.objects.get_or_create(
            session_id=session.session_id.value,
            defaults={"created_at": session.created_at, "last_active": session.last_active},
        )
        # auto_now/auto_now_add son propiedades heredadas del modelo
        # legado; se restauran los timestamps requeridos por la entidad.
        SessionModel.objects.filter(pk=model.pk).update(
            created_at=session.created_at, last_active=session.last_active
        )
        model.refresh_from_db()
        return _session_entity(model)

    def list_expired_before(self, cutoff: datetime) -> tuple[SessionEntity, ...]:
        return tuple(
            _session_entity(model)
            for model in SessionModel.objects.filter(last_active__lt=cutoff)
        )

    def delete(self, session_id: SessionIdentifier) -> None:
        SessionModel.objects.filter(session_id=session_id.value).delete()
