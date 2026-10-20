"""Implementaciones ORM de los contratos de persistencia de usuarios."""

from __future__ import annotations

from django.db.models import F

from apps.users.domain.entities import Profile as ProfileEntity
from apps.users.domain.entities import User as UserEntity
from apps.users.domain.repositories import ProfileRepository, UserRepository
from apps.users.domain.value_objects import EmailAddress, PhoneNumber, UserType

from .models import Profile as ProfileModel
from .models import User as UserModel


def _user_entity(model: UserModel) -> UserEntity:
    return UserEntity(
        id=model.pk,
        email=EmailAddress(model.email),
        first_name=model.first_name,
        last_name=model.last_name,
        is_active=model.is_active,
        user_type=UserType(model.user_type),
    )


def _profile_entity(model: ProfileModel) -> ProfileEntity:
    return ProfileEntity(
        id=model.pk,
        user_id=model.user_id,
        bio=model.bio,
        phone_number=PhoneNumber(model.phone_number) if model.phone_number else None,
        birth_date=model.birth_date,
        entry_date=model.entry_date,
        query_count=model.query_count,
        query_limit=model.query_limit,
    )


class DjangoUserRepository(UserRepository):
    """Mapea ``UserEntity`` al usuario ORM sin exponerlo fuera de infrastructure."""

    def get_by_id(self, user_id: int) -> UserEntity | None:
        model = UserModel.objects.filter(pk=user_id).first()
        return _user_entity(model) if model is not None else None

    def get_by_email(self, email: EmailAddress) -> UserEntity | None:
        model = UserModel.objects.filter(email=str(email)).first()
        return _user_entity(model) if model is not None else None

    def save(self, user: UserEntity) -> UserEntity:
        fields = {
            "email": str(user.email),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "user_type": user.user_type.value,
        }
        if user.id is None:
            model = UserModel.objects.create_user(password=None, **fields)
        else:
            model, _ = UserModel.objects.update_or_create(pk=user.id, defaults=fields)
        return _user_entity(model)


class DjangoProfileRepository(ProfileRepository):
    """Persistencia uno-a-uno de perfiles con actualización atómica de cuota."""

    def get_by_user_id(self, user_id: int) -> ProfileEntity | None:
        model = ProfileModel.objects.filter(user_id=user_id).first()
        return _profile_entity(model) if model is not None else None

    def phone_number_exists(
        self, phone_number: PhoneNumber, *, excluding_profile_id: int | None = None
    ) -> bool:
        query = ProfileModel.objects.filter(phone_number=str(phone_number))
        if excluding_profile_id is not None:
            query = query.exclude(pk=excluding_profile_id)
        return query.exists()

    def save(self, profile: ProfileEntity) -> ProfileEntity:
        defaults = {
            "bio": profile.bio,
            "phone_number": str(profile.phone_number) if profile.phone_number else None,
            "birth_date": profile.birth_date,
            "query_count": profile.query_count,
            "query_limit": profile.query_limit,
        }
        if profile.id is not None:
            model, _ = ProfileModel.objects.update_or_create(
                pk=profile.id, defaults={"user_id": profile.user_id, **defaults}
            )
        else:
            model, _ = ProfileModel.objects.update_or_create(
                user_id=profile.user_id, defaults=defaults
            )
        if profile.entry_date is not None and model.entry_date != profile.entry_date:
            # entry_date es auto_now_add en el esquema histórico; la escritura
            # ORM directa permite mapear una entidad hidratada sin migrar el campo.
            ProfileModel.objects.filter(pk=model.pk).update(entry_date=profile.entry_date)
            model.refresh_from_db()
        return _profile_entity(model)

    def increment_query_count(self, user_id: int) -> None:
        # Registrar cuota no bloquea; crear el perfil faltante conserva la
        # semántica de incremento sin depender de que exista previamente.
        ProfileModel.objects.get_or_create(user_id=user_id)
        ProfileModel.objects.filter(user_id=user_id).update(query_count=F("query_count") + 1)
