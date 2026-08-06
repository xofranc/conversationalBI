# Fase 4 — Migración de autenticación a Supabase Auth

## Objetivo

Reemplazar la autenticación propia de Django REST Framework (DRF SimpleJWT) por **Supabase Auth**. El backend deja de crear/validar usuarios y pasa a **validar los JWT que firma Supabase** contra su JWKS público. El frontend y la futura app iOS (Fase 5) usarán el mismo login de Supabase.

```
Antes:  frontend → /users/login/ → Django valida password → emite JWT
Ahora:  frontend → Supabase Auth (signup/signin) → token
              ↓
        Django: valida JWT (RS256) con JWKS → sincroniza usuario local
```

> **Nota:** Supabase Auth ahora es la única fuente de verdad de identidad. Django conserva el usuario local solo para relacionar datasets, consultas y perfil.

---

## 0. Configuración previa en Supabase Auth

En el dashboard de Supabase (las rutas pueden variar ligeramente según la versión del dashboard):

1. Ve a **Authentication → Sign In / Providers**.
2. Asegúrate de que el proveedor **Email** esté activado (por defecto suele estarlo).
3. En la misma página, dentro de la sección **User Signups**, desactiva el toggle **Confirm email** para que el registro sea inmediato en el TFG.
4. Ve a **Authentication → URL Configuration**:
   - `Site URL`: `https://conversational-bi-eight.vercel.app/`
   - `Redirect URLs`: `https://conversational-bi-eight.vercel.app/*`

Anota para los pasos siguientes:

- `SUPABASE_URL` (ej. `https://xxxx.supabase.co`)
- `SUPABASE_ANON_KEY` (pública, solo para frontend/iOS)

---

## 1. Backend — validación de JWT

### 1.1 Dependencias

Edita `backend/requirements.txt`:

```text
# ELIMINAR
# djangorestframework_simplejwt

# AÑADIR
jwcrypto>=1.5.0
```

Luego instala en local:

```bash
source .venv/bin/activate
pip install jwcrypto>=1.5.0
pip uninstall djangorestframework_simplejwt -y
```

### 1.2 Nuevo autenticador

Crea `backend/apps/users/authentication.py`:

```python
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
            url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
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
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return None

        token = auth[7:]
        try:
            decoded = jwt.JWT(jwt=token, key=self._get_jwks(), algs=['RS256'])
            claims = json.loads(decoded.claims)
        except Exception as e:
            logger.warning("Token inválido: %s", e)
            raise AuthenticationFailed('Token inválido o expirado') from e

        # Preferimos email; si no viene, usamos el UUID de Supabase como identidad
        email = claims.get('email') or f"{claims['sub']}@supabase.local"
        metadata = claims.get('user_metadata', {})

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': metadata.get('first_name', '')[:30],
                'last_name': metadata.get('last_name', '')[:30],
            }
        )
        if not created:
            user.first_name = metadata.get('first_name', user.first_name)[:30]
            user.last_name = metadata.get('last_name', user.last_name)[:30]
            user.save(update_fields=['first_name', 'last_name'])

        # Asegurar que exista el perfil asociado
        Profile.objects.get_or_create(user=user)

        return (user, token)
```

### 1.3 Ajustes en `backend/config/settings.py`

En `INSTALLED_APPS`, eliminar:

```python
'rest_framework_simplejwt.token_blacklist',
```

En `REST_FRAMEWORK`, reemplazar el autenticador:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.users.authentication.SupabaseAuth',
    ],
    # ... resto de DEFAULT_PERMISSION_CLASSES, etc.
}
```

Eliminar todo el bloque:

```python
SIMPLE_JWT = { ... }
```

Añadir al final:

```python
SUPABASE_URL = env('SUPABASE_URL', default='')
```

Añadir a `backend/.env` y `backend/.env.example`:

```bash
# Backend: solo necesita SUPABASE_URL para bajar el JWKS
SUPABASE_URL=https://xxxx.supabase.co
```

> El backend **NO** necesita `SUPABASE_ANON_KEY`; solo se usa en el frontend/iOS.

### 1.4 URLs

Edita `backend/apps/users/urls.py` para quedar solo con el perfil:

```python
from django.urls import path
from .views.profile import ProfileView

urlpatterns = [
    path('profile/', ProfileView.as_view(), name='profile'),
]
```

### 1.5 Archivos a eliminar

Ya no se usan:

```text
backend/apps/users/views/auth.py
backend/apps/users/serializers/auth.py
backend/apps/users/services/auth_service.py
backend/apps/users/tests/test_auth.py
```

### 1.6 Tests nuevos

Reemplaza `backend/apps/users/tests/test_auth.py` por tests de `SupabaseAuth`.

Ejemplo completo usando `jwcrypto` para generar el par de claves y `monkeypatch` para mockear el JWKS:

```python
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
```

---

## 2. Frontend — `@supabase/supabase-js`

### 2.1 Instalar

```bash
cd frontend
npm install @supabase/supabase-js
```

### 2.2 Cliente de Supabase

Crea `frontend/src/supabase.js`:

```js
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
```

### 2.3 Actualizar `frontend/src/api.js`

Reemplaza el manejo de `localStorage` por sesión de Supabase:

```js
import { supabase } from './supabase.js';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

export const api = {
  async getToken() {
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token;
  },

  async _fetch(endpoint, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    const token = await this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    if (options.body instanceof FormData) {
      delete headers['Content-Type'];
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, { ...options, headers });
    if (response.status === 204) return { response, data: null };
    const data = await response.json().catch(() => ({}));
    return { response, data };
  },

  async request(endpoint, options = {}) {
    const { response, data } = await this._fetch(endpoint, options);
    if (!response.ok) throw { status: response.status, data };
    return data;
  },

  auth: {
    register: (email, password, firstName, lastName) =>
      supabase.auth.signUp({
        email,
        password,
        options: {
          data: { first_name: firstName, last_name: lastName },
        },
      }),

    login: (email, password) =>
      supabase.auth.signInWithPassword({ email, password }),

    logout: () => supabase.auth.signOut(),
  },

  dataset: {
    upload: (file, name) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('name', name);
      return api.request('/dataset/', { method: 'POST', body: formData });
    },
    list: () => api.request('/dataset/'),
    delete: (id) => api.request(`/dataset/${id}/`, { method: 'DELETE' }),
  },

  query: {
    ask: (question, datasetId) =>
      api.request('/queries/', {
        method: 'POST',
        body: JSON.stringify({ question, dataset_id: datasetId }),
      }),
    history: (datasetId) =>
      api.request(`/queries/${datasetId ? `?dataset_id=${datasetId}` : ''}`),
    detail: (id) => api.request(`/queries/${id}/`),
  },
};
```

### 2.4 Actualizar `frontend/src/main.js`

Importa Supabase:

```js
import { supabase } from './supabase.js';
```

Al iniciar la app:

```js
const { data: { session } } = await supabase.auth.getSession();
if (session) enterDashboard(false);
```

Login:

```js
loginForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;

  errorEl.classList.add('hidden');
  animations.showLoader('Iniciando sesión...');

  const { error } = await api.auth.login(email, password);
  if (error) {
    animations.hideLoader();
    errorEl.innerText = error.message || 'Error al iniciar sesión.';
    errorEl.classList.remove('hidden');
    return;
  }

  animations.hideLoader();
  enterDashboard(true);
});
```

Registro:

```js
registerForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const firstName = document.getElementById('reg-first-name').value;
  const lastName = document.getElementById('reg-last-name').value;
  const email = document.getElementById('reg-email').value;
  const password = document.getElementById('reg-password').value;

  errorEl.classList.add('hidden');
  animations.showLoader('Creando cuenta...');

  const { error } = await api.auth.register(email, password, firstName, lastName);
  if (error) {
    animations.hideLoader();
    errorEl.innerText = error.message || 'Error al crear la cuenta.';
    errorEl.classList.remove('hidden');
    return;
  }

  animations.hideLoader();
  enterDashboard(true);
});
```

Logout:

```js
document.getElementById('logout-btn').addEventListener('click', async () => {
  await api.auth.logout();
  forceLogout();
});
```

Escucha cambios de sesión:

```js
supabase.auth.onAuthStateChange((event, session) => {
  if (event === 'SIGNED_OUT' || !session) {
    forceLogout();
  }
});
```

### 2.5 Variables de entorno del frontend

Añade a `frontend/.env.example`:

```bash
VITE_API_URL=/api/v1
VITE_SUPABASE_URL=https://xxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...
```

Y en el dashboard de Vercel:

```bash
VITE_SUPABASE_URL=https://xxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...
```

---

## 3. Render (backend)

Añade en el dashboard de Render:

```bash
SUPABASE_URL=https://xxxx.supabase.co
```

Luego redeploya.

---

## 4. Checklist de verificación

### Local

1. `cd backend && python -m pytest` → todos verdes.
2. Iniciar frontend con `npm run dev`.
3. Registro/login → Supabase crea el usuario.
4. `GET /api/v1/users/profile/` devuelve el perfil.
5. Subir CSV y hacer una consulta → `request.user` está correctamente sincronizado.

### Producción

1. Registro en Vercel → el usuario aparece en **Supabase Auth → Users**.
2. Login → la web entra al dashboard.
3. Subir CSV → dataset creado bajo el usuario.
4. Consulta → funciona (cuando el saldo de OpenCode Go esté recargado).
5. Logout → vuelve a la pantalla de login.

---

## 5. Decisiones de diseño

### ¿Email o UUID de Supabase para sincronizar el usuario local?

- **Email (más simple):** el esquema mostrado arriba. Problema: si el usuario cambia su email en Supabase, Django crea un usuario nuevo.
- **UUID de Supabase (más robusto):** agregar `supabase_uid = models.CharField(max_length=36, unique=True, null=True)` al modelo `User`, migrar, y usar `claims['sub']` como lookup. Recomendado para la app iOS en Fase 5.

### ¿Seguir usando el admin de Django?

- El admin de Django usa sesiones de Django, no tokens JWT.
- Si quieres seguir accediendo a `/admin/`, mantén `django.contrib.auth.backends.ModelBackend` en `AUTHENTICATION_BACKENDS` y crea un superusuario con `python manage.py createsuperuser`.
- La API pública seguirá usando `SupabaseAuth`.

---

## 6. Errores comunes

| Error | Causa probable | Solución |
|---|---|---|
| `Token inválido o expirado` | `SUPABASE_URL` mal configurada o el token expiró | Verifica `SUPABASE_URL` en Render; refresca el token en el frontend |
| `400 User already registered` | Supabase Auth no permite email duplicado | Muestra el mensaje de error de Supabase |
| CORS error en frontend | El backend rechaza el origen de Vercel | Verifica `CORS_ALLOWED_ORIGINS` en Render |
| `first_name` / `last_name` vacíos | El frontend no los envió en `user_metadata` | Revisa `signUp({ options: { data: { first_name, last_name } } })` |
| `User has no profile` | Se llamó `user.profile` pero no se creó | En `ProfileView` se usa `get_or_create`; el autenticador también puede crearlo explícitamente |

---

## 7. Cambios en URLs del backend

Antes | Después
---|---
`POST /api/v1/users/register/` | `supabase.auth.signUp()` en el frontend
`POST /api/v1/users/login/` | `supabase.auth.signInWithPassword()` en el frontend
`POST /api/v1/users/logout/` | `supabase.auth.signOut()` en el frontend
`POST /api/v1/users/token/refresh/` | Manejado automáticamente por Supabase
`GET /api/v1/users/profile/` | Se mantiene ✅

---

**Estado:** guía de implementación para la Fase 4 del `PLAN_MIGRACION.md`.
