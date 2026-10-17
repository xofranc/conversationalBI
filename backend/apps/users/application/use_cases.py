"""Casos de uso de perfil, acceso y cuota informativa."""

from __future__ import annotations

from dataclasses import replace

from apps.dataset.domain.policies import DatasetOwnershipPolicy
from apps.dataset.domain.repositories import DatasetRepository
from apps.users.domain.entities import Profile
from apps.users.domain.repositories import ProfileRepository
from apps.users.domain.value_objects import PhoneNumber

from .dtos import (
    AccessDecisionDTO,
    AuthenticateInput,
    AuthenticatedIdentityDTO,
    CanAccessDatasetInput,
    GetProfileInput,
    GetQuotaInput,
    ProfileDTO,
    QuotaDTO,
    UpdateProfileInput,
)
from .ports import ExternalAuthenticator


def _profile_dto(profile: Profile) -> ProfileDTO:
    return ProfileDTO(
        user_id=profile.user_id,
        bio=profile.bio,
        phone_number=str(profile.phone_number) if profile.phone_number else None,
        birth_date=profile.birth_date,
        entry_date=profile.entry_date,
    )


class GetProfile:
    """Obtiene o inicializa el perfil asociado al usuario."""

    def __init__(self, profiles: ProfileRepository) -> None:
        self._profiles = profiles

    def execute(self, request: GetProfileInput) -> ProfileDTO:
        profile = self._profiles.get_by_user_id(request.user_id)
        if profile is None:
            profile = self._profiles.save(Profile(user_id=request.user_id))
        return _profile_dto(profile)


class UpdateProfile:
    """Actualiza exclusivamente los campos indicados por el llamador."""

    def __init__(self, profiles: ProfileRepository) -> None:
        self._profiles = profiles

    def execute(self, request: UpdateProfileInput) -> ProfileDTO:
        profile = self._profiles.get_by_user_id(request.user_id)
        if profile is None:
            profile = Profile(user_id=request.user_id)

        changes: dict[str, object] = {}
        if request.update_bio:
            changes["bio"] = request.bio or ""
        if request.update_phone_number:
            phone = PhoneNumber(request.phone_number) if request.phone_number else None
            if phone and self._profiles.phone_number_exists(
                phone, excluding_profile_id=profile.id
            ):
                raise ValueError("El número de teléfono ya está registrado")
            changes["phone_number"] = phone
        if request.update_birth_date:
            changes["birth_date"] = request.birth_date

        updated = replace(profile, **changes)
        return _profile_dto(self._profiles.save(updated))


class GetQuota:
    """Expone el uso de cuota como información; nunca bloquea consultas."""

    def __init__(self, profiles: ProfileRepository) -> None:
        self._profiles = profiles

    def execute(self, request: GetQuotaInput) -> QuotaDTO:
        profile = self._profiles.get_by_user_id(request.user_id)
        if profile is None:
            return QuotaDTO(query_count=0, query_limit=0, available=False)
        return QuotaDTO(
            query_count=profile.query_count,
            query_limit=profile.query_limit,
            available=profile.can_query,
        )


class CanAccessDataset:
    """Comprueba ownership a partir del identificador del propietario."""

    def __init__(self, datasets: DatasetRepository) -> None:
        self._datasets = datasets

    def execute(self, request: CanAccessDatasetInput) -> AccessDecisionDTO:
        dataset = self._datasets.get_by_id(request.dataset_id)
        return AccessDecisionDTO(
            allowed=dataset is not None and DatasetOwnershipPolicy.owns(dataset, request.user_id)
        )


class AuthenticateExternalIdentity:
    """Delegación pura al puerto de autenticación; no valida tokens aquí."""

    def __init__(self, authenticator: ExternalAuthenticator) -> None:
        self._authenticator = authenticator

    def execute(self, request: AuthenticateInput) -> AuthenticatedIdentityDTO | None:
        identity = self._authenticator.authenticate(request.credential)
        if identity is None:
            return None
        # Compatibilidad temporal con implementaciones del contrato anterior.
        if isinstance(identity, tuple):
            user_id, email = identity
        else:
            user_id, email = identity.user_id, identity.email
        return AuthenticatedIdentityDTO(
            user_id=user_id,
            email=email,
        )


class IncrementQueryUsage:
    """Registra uso sin consultar ni aplicar el límite."""

    def __init__(self, profiles: ProfileRepository) -> None:
        self._profiles = profiles

    def execute(self, user_id: int) -> None:
        self._profiles.increment_query_count(user_id)
