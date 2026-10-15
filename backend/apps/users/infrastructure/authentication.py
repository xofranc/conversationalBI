"""Adaptador DRF para autenticar mediante el caso de uso de usuarios."""

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import User as DjangoUser


class SupabaseAuth(BaseAuthentication):
    """Valida Supabase mediante application y retorna el modelo Django a DRF."""

    _jwks_cache = None

    def authenticate(self, request):
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            return None

        token = authorization[7:]

        # Imports locales: el composition root construye este adaptador y así
        # se evita un ciclo entre composition, el adaptador DRF y el port.
        from apps.users.application.dtos import AuthenticateInput
        from apps.users.infrastructure.adapters import (
            SupabaseAuthenticationError,
            SupabaseAuthenticator,
        )
        from apps.users.infrastructure.composition import build_user_use_cases

        if self.__class__._jwks_cache is None:
            SupabaseAuthenticator._jwks_cache = None

        try:
            authenticate_identity = build_user_use_cases()["authenticate"]
            identity = authenticate_identity.execute(AuthenticateInput(credential=token))
        except SupabaseAuthenticationError as error:
            raise AuthenticationFailed(str(error)) from error
        finally:
            self.__class__._jwks_cache = SupabaseAuthenticator._jwks_cache

        if identity is None:
            return None

        # Resuelve la identidad escalar a un usuario ORM solo en infrastructure,
        # que es el objeto que espera el contrato de autenticación de DRF.
        user = DjangoUser.objects.get(pk=identity.user_id)
        return user, token
