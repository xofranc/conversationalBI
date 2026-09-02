import json
import logging

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from jwcrypto import jwk, jwt
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from apps.users.models import Profile

logger = logging.getLogger(__name__)
User = get_user_model()


class SupabaseAuth(BaseAuthentication):
    """
    Valida access tokens de Supabase Auth (JWT RS256) contra el JWKS público.
    Crea o actualiza el usuario local en Django bajo demanda.
    """

    _jwks_cache = None

    def _get_jwks(self):
        if SupabaseAuth._jwks_cache is None:
            supabase_url = settings.SUPABASE_URL
            if not supabase_url:
                logger.error("SUPABASE_URL no está configurada")
                raise AuthenticationFailed(
                    "SUPABASE_URL no está configurada en el backend"
                )
            url = f"{supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
            try:
                resp = requests.get(url, timeout=5)
                resp.raise_for_status()
            except requests.RequestException as e:
                logger.error("Error obteniendo JWKS de Supabase: %s", e)
                raise AuthenticationFailed(
                    "No se pudo obtener las claves de validación de Supabase"
                ) from e
            SupabaseAuth._jwks_cache = jwk.JWKSet.from_json(resp.text)
        return SupabaseAuth._jwks_cache

    def authenticate(self, request):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None

        token = auth[7:]
        try:
            decoded = jwt.JWT(jwt=token, key=self._get_jwks(), algs=["RS256"])
            claims = json.loads(decoded.claims)
        except Exception as e:
            logger.warning("Token inválido: %s", e)
            raise AuthenticationFailed("Token inválido o expirado") from e

        # Preferimos email; si no viene, usamos el UUID de Supabase como identidad
        email = claims.get("email") or f"{claims['sub']}@supabase.local"
        metadata = claims.get("user_metadata", {})

        user, created = User.objects.get_or_create(
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

        # Asegurar que exista el perfil asociado
        Profile.objects.get_or_create(user=user)

        return (user, token)
