"""Adaptador DRF para autenticar mediante Supabase en infrastructure."""

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .adapters import SupabaseAuthenticationError, SupabaseAuthenticator
from .models import User as DjangoUser


class SupabaseAuth(BaseAuthentication):
    """Valida Supabase y retorna el modelo Django que requiere DRF."""

    def authenticate(self, request):
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            return None

        token = authorization[7:]

        try:
            identity = SupabaseAuthenticator().authenticate(token)
        except SupabaseAuthenticationError as error:
            raise AuthenticationFailed(str(error)) from error

        if identity is None:
            return None

        # Resuelve la identidad escalar a un usuario ORM solo en infrastructure,
        # que es el objeto que espera el contrato de autenticación de DRF.
        user = DjangoUser.objects.get(pk=identity.user_id)
        return user, token
