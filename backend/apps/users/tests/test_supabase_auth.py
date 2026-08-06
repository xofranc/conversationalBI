# backend/apps/users/tests/test_supabase_auth.py
import json
from datetime import datetime, timedelta, timezone

import pytest
from django.conf import settings
from jwcrypto import jwk, jwt
from rest_framework import status

from apps.users.authentication import SupabaseAuth


@pytest.fixture
def valid_supabase_token(monkeypatch):
    """Genera un JWT firmado con una clave RSA de prueba y mockea el JWKS."""

    # 1. Par de claves RSA de prueba
    key = jwk.JWK.generate(kty="RSA", size=2048)

    # 2. Construir JWKS con la clave pública
    public_jwk = json.loads(key.export_public())
    public_jwk.update({
        "kty": "RSA",
        "kid": "test-key-1",
        "use": "sig",
        "alg": "RS256",
    })
    jwks = {"keys": [public_jwk]}

    # 3. Mockear requests.get para que devuelva el JWKS de prueba
    class FakeResponse:
        def raise_for_status(self):
            pass

        @property
        def text(self):
            return json.dumps(jwks)

    monkeypatch.setattr(
        "apps.users.authentication.requests.get",
        lambda url, timeout=None: FakeResponse(),
    )

    # 4. Forzar una URL de Supabase de prueba y limpiar caché de JWKS
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://test-project.supabase.co")
    SupabaseAuth._jwks_cache = None

    # 5. Generar un JWT firmado con la clave privada de prueba
    now = datetime.now(timezone.utc)
    claims = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "email": "test@example.com",
        "user_metadata": {
            "first_name": "Test",
            "last_name": "User",
        },
        "exp": int((now + timedelta(minutes=5)).timestamp()),
        "iat": int(now.timestamp()),
    }

    token = jwt.JWT(
        header={"alg": "RS256", "typ": "JWT", "kid": "test-key-1"},
        claims=claims,
    )
    token.make_signed_token(key)
    return token.serialize()


@pytest.mark.django_db
class TestSupabaseAuth:
    def test_token_valido_crea_usuario(self, api_client, valid_supabase_token):
        response = api_client.get(
            "/api/v1/users/profile/",
            HTTP_AUTHORIZATION=f"Bearer {valid_supabase_token}",
        )
        assert response.status_code == status.HTTP_200_OK

        # Verificar que el usuario se creó localmente con los datos del token
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.get(email="test@example.com")
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.profile is not None
