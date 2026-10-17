"""Adaptadores de autenticación externa para application.users."""

from __future__ import annotations

import json
import logging

import requests
from django.conf import settings
from jwcrypto import jwk, jwt

from apps.users.domain.value_objects import AuthenticatedIdentity

from .models import Profile as ProfileModel
from .models import User as UserModel

logger = logging.getLogger(__name__)


class SupabaseAuthenticationError(Exception):
    """Error traducible a una respuesta de autenticación en infrastructure."""


class SupabaseAuthenticator:
    """Valida JWT de Supabase y provisiona el usuario Django correspondiente.

    Este adaptador implementa ``ExternalAuthenticator``. Su resultado expone
    únicamente escalares; los modelos Django permanecen dentro de
    infrastructure.
    """

    _jwks_cache = None

    def _get_jwks(self):
        if SupabaseAuthenticator._jwks_cache is None:
            supabase_url = settings.SUPABASE_URL
            if not supabase_url:
                logger.error("SUPABASE_URL no está configurada")
                raise SupabaseAuthenticationError(
                    "SUPABASE_URL no está configurada en el backend"
                )

            url = f"{supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
            except requests.RequestException as error:
                logger.error("Error obteniendo JWKS de Supabase: %s", error)
                raise SupabaseAuthenticationError(
                    "No se pudo obtener las claves de validación de Supabase"
                ) from error

            SupabaseAuthenticator._jwks_cache = jwk.JWKSet.from_json(response.text)
        return SupabaseAuthenticator._jwks_cache

    def authenticate(self, credential: str) -> AuthenticatedIdentity | None:
        if not credential:
            return None

        try:
            decoded = jwt.JWT(jwt=credential, key=self._get_jwks(), algs=["RS256"])
            claims = json.loads(decoded.claims)
        except Exception as error:
            # Mantiene el error público histórico para JWT inválidos/expirados.
            logger.warning("Token inválido: %s", error)
            raise SupabaseAuthenticationError("Token inválido o expirado") from error

        # Preferimos email; si falta, usamos el UUID de Supabase como identidad.
        email = claims.get("email") or f"{claims['sub']}@supabase.local"
        metadata = claims.get("user_metadata", {})

        user, created = UserModel.objects.get_or_create(
            email=email,
            defaults={
                "first_name": metadata.get("first_name", "")[:30],
                "last_name": metadata.get("last_name", "")[:30],
            },
        )
        if not created:
            user.first_name = metadata.get("first_name", user.first_name)[:30]
            user.last_name = metadata.get("last_name", user.last_name)[:30]
            user.save(update_fields=["first_name", "last_name"])

        ProfileModel.objects.get_or_create(user=user)
        return AuthenticatedIdentity(user_id=int(user.pk), email=str(user.email))
