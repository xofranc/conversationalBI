# Plan de Migración — ConversationalBI

> **Estado de ejecución (01/08/2026):**
> - **Fase 0** ✅ cuentas y env vars (OpenCode Go + Supabase)
> - **Fase 1** ✅ código migrado a `LLMClient` (OpenAI-compatible); 157 tests verdes. Bloqueo menor: saldo de OpenCode Go agotado (`CreditsError`) — la ruta LLM E2E queda pendiente de recarga
> - **Fase 2** ✅ **verificada E2E contra Supabase**: migraciones aplicadas, rol `bi_reader` creado (login por pooler con sufijo `.<project-ref>`), upload CSV → schema `ds_1` (900 filas, GRANT SELECT automático), consulta resumen leyendo vía read-only, INSERT bloqueado por privilegios
> - **Tests**: guard en `settings.py` (bloque `_TESTING`) — `pytest` nunca toca la BD del `.env` (protege Supabase prod). Por defecto: 135 verdes + 22 skips (SQLite). Suite completa: `CBI_TEST_DATABASE_URL=...local... CBI_TEST_DATABASE_READER_URL=...local... pytest` → 157 verdes
> - **Fase 3** 🔶 endpoint `/api/v1/health/` + `render.yaml` (Blueprint) listos; landing actualizada al stack cloud (copy "local" eliminado); falta: crear servicio en Render, deploy Vercel, cron anti cold-start
> - **Fases 4-6** ❌ pendientes

**Objetivo:** Migrar de stack local (Ollama + SQLite + docker-compose) a cloud (OpenCode Go + Supabase Postgres/Auth + Render + Vercel + iOS SwiftUI), y desplegar a producción.

**Decisiones tomadas (31/07/2026):**

| Decisión | Elección |
|---|---|
| LLM | **OpenCode Go** (suscripción activa, $10/mes) — endpoint OpenAI-compatible |
| Base de datos | **Supabase Postgres** (app DB + schema por dataset) |
| Auth | **Supabase Auth** + validación JWKS en Django |
| Hosting | **Render** (API) + **Vercel** (frontend), plan gratis |
| App móvil | **SwiftUI nativo** + Swift Charts |

---

## Arquitectura final

```
[Web Vite+Chart.js (Vercel)] ─┐
[iOS SwiftUI (supabase-swift)]┤─► Supabase Auth (JWT) ─► Django API (Render) ─► Supabase Postgres
                                                           │                     ├─ BD app (schema public)
   OpenCode Go API ◄───────────────────────────────────────┘                     └─ schemas ds_{id} (datasets)
   kimi-k2.7-code → SQL | mimo-v2.5 → respuestas
```

### Stack: antes → después

| Capa | Antes | Después |
|---|---|---|
| **LLM** | Ollama qwen2.5-coder:7b (local, 15-40s/consulta) | OpenCode Go API (1-3s/consulta) |
| **BD app** | SQLite (`db.sqlite3`) | Supabase Postgres (500 MB gratis) |
| **BD datasets** | SQLite por dataset (`media/dbs/`) | Schema Postgres por dataset (`ds_{id}`) |
| **Auth** | DRF SimpleJWT | Supabase Auth + JWKS en Django |
| **File storage** | `media/` local | Supabase Storage (Fase 6, opcional) |
| **Caché** | LocMemCache | LocMemCache (se mantiene) |
| **Deploy** | docker-compose local | Render + Vercel (GitOps) |
| **iOS** | No existe | SwiftUI nativo |

---

## Estado actual verificado (31/07/2026)

Nada del plan anterior está ejecutado. Superficie de cambio real:

- **Ollama:** solo `services/ai/sql_agent.py` y `services/ai/answer_writer.py` usan `OllamaLLM` + vars `OLLAMA_*` en `settings.py` + 1 línea en `apps/queries/services/query_service.py:102`
- **SQLite:** `settings.py` (DATABASES), `database_service.py` (materialize/read/delete a `media/dbs/dataset_<id>.sqlite` con conexión read-only), `sql_executor.py` (`_connect` + sandbox en memoria), `analysis_service.py` (`read_tables`), `dataset_service.py`, `query_service.py` (re-materialización)
- **Auth:** SimpleJWT en settings + `apps/users/views/auth.py`, `serializers/auth.py`, `services/auth_service.py`
- **Tests:** 156 totales; los de IA usan LLMs falsos, los de DB usan SQLite → se actualizan en cada fase

---

## OpenCode Go — datos verificados (docs oficiales)

- **Endpoint:** `https://opencode.ai/zen/go/v1/chat/completions` (OpenAI-compatible) con `Authorization: Bearer <API_KEY>`
- **API key:** consola en [opencode.ai/auth](https://opencode.ai/auth)
- **Límites de la suscripción:** $12 / 5h · $30 / semana · **$60 / mes**

### Modelos elegidos (retención 0 días, no entrenan con tus datos)

| Rol | Modelo | Precio/1M tok (in/out) | Capacidad aprox |
|---|---|---|---|
| SQL generation | `kimi-k2.7-code` | $0.95 / $4.00 | ~1.350 req/5h |
| Answer writer | `mimo-v2.5` | $0.14 / $0.28 | ~30.000 req/5h |

**Costo por consulta BI** (~2K tokens in + 2 llamadas): ~$0.003 → **$60/mes ≈ ~20.000 consultas/mes**. Sobrado para el TFG.

⚠️ **Evitar `deepseek-v4-flash`**: es el único modelo de Go que SÍ entrena con los datos del usuario.
⚠️ **Sin lock-in:** el cliente LLM es agnóstico (SDK `openai` + `base_url` configurable). Cambiar a Groq/OpenRouter/Ollama = cambiar env vars, sin tocar código.

---

## Línea de tiempo

```
Fase 0 ─► Fase 1 ─► Fase 2 ─► Fase 3 ─► Fase 4 ─► Fase 5 ─► Fase 6
 30min     2-3h       4-5h      2h        3-4h      ~24h      2h
                                   ▲
                          WEB EN PRODUCCIÓN AQUÍ
```

El deploy (Fase 3) va ANTES del auth (Fase 4): valida primero lo más riesgoso (pooler, migraciones, CORS) con el auth que ya funciona. Sin usuarios reales, el swap de auth después es transparente.

---

## Fase 0: Setup de cuentas (~30 min, manual)

| Servicio | Qué obtener |
|---|---|
| **OpenCode Go** | API key (`sk-...`) en opencode.ai/auth |
| **Supabase** | Proyecto → `URL`, `ANON_KEY`, `SERVICE_ROLE_KEY`, `DATABASE_URL` (pooler, puerto 5432) |

**`backend/.env`** (nuevas vars; las de Ollama se eliminan en Fase 1):

```bash
# LLM (agnóstico de proveedor)
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://opencode.ai/zen/go/v1
LLM_SQL_MODEL=kimi-k2.7-code
LLM_ANSWER_MODEL=mimo-v2.5
LLM_TIMEOUT=60

# Supabase
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJxxx
SUPABASE_SERVICE_KEY=eyJxxx
DATABASE_URL=postgres://postgres.xxxx:pass@aws-0-xxx.pooler.supabase.com:5432/postgres

# Django (ya existen)
SECRET_KEY=django-insecure-xxx
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

---

## Fase 1: LLM — Ollama → OpenCode Go (~2-3h) ⚡ quick win

Mayor impacto inmediato: de 15-40s a 1-3s por consulta. Se prueba en local sin tocar la BD.

### 1.1 Nuevo `backend/services/ai/llm_client.py`

```python
from openai import OpenAI
from django.conf import settings

class LLMClient:
    """Cliente agnóstico: cualquier endpoint OpenAI-compatible
    (OpenCode Go, Groq, OpenRouter, Ollama). Se cambia por env vars."""
    def __init__(self, model: str, temperature: float, max_tokens: int, stop: list):
        self.client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL,
                             timeout=settings.LLM_TIMEOUT)
        self.model, self.temperature = model, temperature
        self.max_tokens, self.stop = max_tokens, stop

    def complete(self, prompt: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model, temperature=self.temperature,
            max_tokens=self.max_tokens, stop=self.stop,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content or ''
```

### 1.2 Cambios mínimos

- **`sql_agent.py`**: `self.llm = LLMClient(settings.LLM_SQL_MODEL, temperature=0, max_tokens=220, stop=['\n\n','PREGUNTA:','Pregunta:','Ejemplo:','/*'])`; `run()` llama `self.llm.complete(prompt)`. `_clean()` no cambia.
- **`answer_writer.py`**: mismo patrón con `LLM_ANSWER_MODEL`, `temperature=0.3`, `max_tokens=160`, stops actuales. Fallback determinista no cambia.
- **`settings.py`**: reemplazar bloque `OLLAMA_*` por las 5 vars `LLM_*` (via `env()`).
- **`query_service.py:102`**: fallback `model_used` → `settings.LLM_SQL_MODEL`.

### 1.3 requirements.txt

```
# QUITAR (5): langchain-ollama, ollama, langchain-core, langsmith, langchain-protocol
# AÑADIR (1): openai>=1.50.0
```

### 1.4 Verificación

- Actualizar `services/ai/tests/` (mocks sobre `LLMClient.complete`, misma interfaz que hoy: `writer.llm = _LLMFalso(...)` sigue funcionando si el fake expone `complete` → ajustar a `invoke`→`complete`).
- Los 156 tests en verde + consulta real end-to-end en local.
- docker-compose: eliminar servicio `ollama` y vars `OLLAMA_*` (ya no aplica).

---

## Fase 2: Postgres en Supabase (~4-5h)

### 2.1 Settings — BD app

```python
DATABASES = {
    'default': {
        **env.db('DATABASE_URL'),   # django-environ parsea la URL del pooler
        'OPTIONS': {'options': '-c statement_timeout=30000'},
    }
}
```

Migraciones existentes corren sin cambios (mismo schema Django, otro engine): `python manage.py migrate`.

### 2.2 `database_service.py` — reescritura (SQLite → schemas Postgres)

- `materialize(dataset_id, abs_file_path)` → crea schema `ds_{id}`, una tabla por hoja/archivo, bulk insert con `psycopg2.extras.execute_values`. Retorna `'ds_{id}'` (se guarda en `Dataset.db_path`).
- `delete(db_path)` → `DROP SCHEMA ds_{id} CASCADE`.
- `read_tables(db_path)` → `information_schema.tables` del schema + `pd.read_sql_query` por tabla.
- `_DTYPE_MAP`: pandas dtype → tipo Postgres (`BIGINT`, `DOUBLE PRECISION`, `TEXT`, `BOOLEAN`, `TIMESTAMP`).

```python
schema = f'ds_{dataset_id}'
conn = psycopg2.connect(settings.DATABASE_URL); conn.autocommit = True
cur = conn.cursor()
cur.execute(f'CREATE SCHEMA IF NOT EXISTS {schema}')
for name, df in tables.items():
    clean = name.replace('"', '""').replace('.', '_')
    cols = ', '.join(f'"{c}" {_DTYPE_MAP[str(df[c].dtype)]}' for c in df.columns)
    cur.execute(f'DROP TABLE IF EXISTS {schema}."{clean}"')
    cur.execute(f'CREATE TABLE {schema}."{clean}" ({cols})')
    rows = [tuple(None if pd.isna(v) else v for v in r) for r in df.values]
    execute_values(cur, f'INSERT INTO {schema}."{clean}" ({cols_list}) VALUES %s', rows)
conn.close()
return schema
```

### 2.3 `sql_executor.py` y `analysis_service.py`

```python
conn = psycopg2.connect(settings.DATABASE_URL)
with conn.cursor() as cur:
    cur.execute(f'SET search_path TO {dataset.db_path}')
```

El sandbox en memoria de `sql_executor._connect` (datasets legacy sin `db_path`) desaparece: todo dataset pasa por `materialize()`.

### 2.4 Seguridad: rol read-only (mejora sobre el plan anterior)

Conserva la defensa en profundidad que hoy da la conexión SQLite read-only:

```sql
-- Una vez, en el SQL editor de Supabase:
CREATE ROLE bi_reader LOGIN PASSWORD 'xxx';
GRANT USAGE ON SCHEMA ds_1 TO bi_reader;           -- por schema, al materializar
GRANT SELECT ON ALL TABLES IN SCHEMA ds_1 TO bi_reader;
```

- Escritura (materialize/delete): conexión con rol postgres (DATABASE_URL).
- Lectura (sql_executor/analysis): conexión con `bi_reader` (`DATABASE_READER_URL`).

### 2.5 requirements.txt

```
# AÑADIR: psycopg2-binary>=2.9.0
```

### 2.6 Verificación

Tests de `database_service`/`sql_executor` contra Postgres local o Supabase directo + subir CSV de `samples/` y consultar end-to-end.

---

## Fase 3: Deploy web (~2h) 🚀 producción

### 3.1 Render — API

Web Service desde GitHub:

| Campo | Valor |
|---|---|
| Build | `pip install -r requirements.txt && python manage.py migrate` |
| Start | `gunicorn config.wsgi:application --workers 1 --threads 2 --timeout 120` |
| Plan | Free |
| Health check | `/api/v1/health/` (endpoint nuevo: retorna 200 `{"status":"ok"}`) |

Env vars: `LLM_*`, `SUPABASE_*`, `DATABASE_URL`, `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS=.onrender.com`, `CORS_ALLOWED_ORIGINS=https://<app>.vercel.app`.

### 3.2 Vercel — Frontend

Importar `frontend/` (Vite): build `npm run build`, output `dist/`. Env: `VITE_API_URL=https://<api>.onrender.com/api/v1` (+ `VITE_SUPABASE_*` en Fase 4).

### 3.3 Anti cold-start

Render free duerme tras inactividad (~30-60s de arranque). **cron-job.org** → GET a `/api/v1/health/` cada 10 min. Gratis y elimina el problema en demos.

### 3.4 render.yaml (infra como código, opcional)

```yaml
services:
  - type: web
    name: conversationalbi-api
    env: python
    buildCommand: pip install -r requirements.txt && python manage.py migrate
    startCommand: gunicorn config.wsgi:application --workers 1 --threads 2 --timeout 120
    healthCheckPath: /api/v1/health/
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: "false"
      - key: LLM_API_KEY
        sync: false
      - key: DATABASE_URL
        sync: false
```

### 3.5 Verificación

Flujo completo en URLs públicas: registro → login → upload CSV → consulta → gráfica → historial.

---

## Fase 4: Supabase Auth (~3-4h)

### 4.1 Backend — validación JWKS

Supabase firma JWTs con **RS256** (llaves rotables). Django valida contra `https://<proyecto>.supabase.co/auth/v1/.well-known/jwks.json`.

**Nuevo `backend/apps/users/authentication.py`:**

```python
class SupabaseAuth(BaseAuthentication):
    _jwks_cache = None

    def _get_jwks(self):
        if SupabaseAuth._jwks_cache is None:
            resp = requests.get(f'{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json', timeout=5)
            SupabaseAuth._jwks_cache = jwk.JWKSet.from_json(resp.text)
        return SupabaseAuth._jwks_cache

    def authenticate(self, request):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return None
        try:
            decoded = jwt.JWT(jwt=auth[7:], key=self._get_jwks(), algs=['RS256'])
            claims = json.loads(decoded.claims)
        except Exception:
            raise AuthenticationFailed('Token inválido o expirado')
        user, _ = User.objects.get_or_create(
            email=claims.get('email', claims['sub']),
            defaults={'first_name': claims.get('user_metadata', {}).get('first_name', ''),
                      'last_name':  claims.get('user_metadata', {}).get('last_name', '')})
        return (user, auth[7:])
```

En settings: `DEFAULT_AUTHENTICATION_CLASSES = ['apps.users.authentication.SupabaseAuth']`. Eliminar bloque `SIMPLE_JWT` y `rest_framework_simplejwt` de INSTALLED_APPS/requirements.

### 4.2 Backend — limpieza

| Eliminar | Reemplazado por |
|---|---|
| `apps/users/views/auth.py` | Supabase Auth SDK |
| `apps/users/serializers/auth.py` | Supabase Auth SDK |
| `apps/users/services/auth_service.py` | Supabase Auth SDK |

`ProfileView` se mantiene (query_count, query_limit). Rutas auth propias fuera de `urls.py`.

### 4.3 Frontend

```
npm i @supabase/supabase-js
```

`src/api.js`: `createClient(VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY)`; `signInWithPassword` / `signUp({options:{data:{first_name,last_name}}})` / `signOut`; header `Authorization: Bearer ${session.access_token}` en cada request. Estado de sesión con `onAuthStateChange` (reemplaza manejo manual de tokens/refresh en `main.js`).

### 4.4 Verificación

Registro + login + logout en la web desplegada; usuario aparece en Supabase dashboard y se sincroniza en tabla `users` de Django.

---

## Fase 5: App iOS — SwiftUI (~24h)

### 5.1 Estructura

```
conversationalBI-ios/
├── App.swift
├── Models/    Dataset.swift · Query.swift · ChartConfig.swift
├── Services/  SupabaseManager.swift (auth singleton + session listener)
│              APIClient.swift (actor, URLSession → Django en Render)
└── Views/     AuthView · HomeView · ChatView · ChartContainer · ReceiptView · HistoryView · ProfileView
```

Dependencias SPM: `supabase-swift` (auth) + Swift Charts (nativo, sin dependencia). iOS 17+.

### 5.2 Piezas clave

- **APIClient**: `actor` con URLSession; inyecta `Bearer` de `supabase.auth.session.accessToken`; `get/post` genéricos con `Codable` (~50 líneas).
- **Charts**: `BarMark` / `PointMark` / `LineMark` según `chart_type` del backend; `.frame(height: 280)`.
- **Chat**: burbujas user/ai, scroll automático, loading indicator durante la consulta.

### 5.3 Pantallas y estimación

| Pantalla | ~h |
|---|---|
| Auth (supabase-swift, mismo auth que la web) | 3h |
| Home (lista datasets, upload CSV con DocumentPicker, delete) | 4h |
| Chat (burbujas, input, loading) | 6h |
| Charts (Swift Charts nativo) | 5h |
| Receipt (SQL monoespaciado expandible) | 2h |
| History + Profile | 4h |
| **Total** | **~24h** |

**No hace falta Apple Developer ($99):** para el TFG basta simulador de Xcode. La cuenta solo es necesaria para App Store/TestFlight externo.

### 5.4 Verificación

Flujo completo en simulador contra la API de Render: login → upload → consulta → gráfica → historial.

---

## Fase 6: Hardening (opcional, ~2h)

1. **Supabase Storage** para CSV originales: el disco de Render free es efímero. Las consultas sobreviven (leen de Postgres), pero los archivos originales se pierden en cada redeploy → `django-storages[s3]` apuntando al endpoint S3 de Supabase, bucket `datasets`.
2. Dominio propio en Vercel/Render.
3. Monitoreo de uso de OpenCode Go en opencode.ai/auth (alertas de presupuesto).

---

## Resumen de archivos

### Modificar

| Archivo | Fase | Cambio |
|---|---|---|
| `backend/requirements.txt` | 1,2,4 | −6 (ollama/langchain×4, simplejwt) +4 (openai, psycopg2-binary, jwcrypto, requests ya está) |
| `backend/config/settings.py` | 1,2,4 | LLM_* en vez de OLLAMA_*; DATABASES→Postgres; SupabaseAuth; −SIMPLE_JWT |
| `backend/services/ai/sql_agent.py` | 1 | OllamaLLM → LLMClient |
| `backend/services/ai/answer_writer.py` | 1 | OllamaLLM → LLMClient |
| `backend/apps/queries/services/query_service.py` | 1 | fallback model_used |
| `backend/apps/dataset/services/database_service.py` | 2 | SQLite → schemas Postgres |
| `backend/services/ai/sql_executor.py` | 2 | sqlite3 → psycopg2 + search_path |
| `backend/services/analysis/analysis_service.py` | 2 | read_tables desde Postgres |
| `backend/apps/dataset/services/dataset_service.py` | 2 | db_path = schema name |
| `backend/apps/users/urls.py` | 4 | solo profile/ |
| `frontend/src/api.js` | 4 | cliente Supabase Auth |
| `frontend/src/main.js` | 4 | onAuthStateChange |
| `frontend/package.json` | 4 | + @supabase/supabase-js |
| `docker-compose.yml` | 1 | − servicio ollama |
| Tests (ai, dataset, queries) | 1,2 | mocks nuevos clientes / Postgres |

### Nuevos

| Archivo | Fase |
|---|---|
| `backend/services/ai/llm_client.py` | 1 |
| Endpoint `/api/v1/health/` | 3 |
| `render.yaml` (opcional) | 3 |
| `backend/apps/users/authentication.py` | 4 |
| `conversationalBI-ios/` | 5 |

### Eliminar (Fase 4)

`apps/users/views/auth.py` · `apps/users/serializers/auth.py` · `apps/users/services/auth_service.py`

### No cambian

`prompt_builder.py` (prompts independientes del LLM) · `apps/queries/` (endpoints, serializers, repos) · `dataset/models.py` (`db_path` ahora guarda schema) · `dataset/views.py` · `chart_selector.py` · `sql_validator.py` · `suggester.py`

---

## Costos y límites

| Servicio | Costo | Límite |
|---|---|---|
| OpenCode Go | $10/mes (ya activo) | $60/mes ≈ ~20.000 consultas — sobrado |
| Supabase | $0 | 500 MB DB · 50k MAU auth · 1 GB storage |
| Render + Vercel | $0 | Cold start mitigado con ping cron |
| Apple Developer | $0 | No necesario (simulador) |
| **Total** | **$10/mes ya pagados** | |

---

## Riesgos y notas

1. **OpenCode Go como backend de app:** endpoints API documentados oficialmente, pero pensados para clientes OpenCode. El `LLMClient` agnóstico permite cambiar a Groq (gratis, 30 req/min) con una env var si surge cualquier problema de límites o términos.
2. **Datasets SQLite actuales** en `media/dbs/` no migran: se re-suben por la UI post-deploy.
3. **`SERVICE_ROLE_KEY`** solo en Django (Render env vars). Jamás al frontend ni a iOS. Frontend e iOS usan `ANON_KEY`.
4. **Pooler de Supabase:** usar el connection string del pooler (puerto 5432, session mode) tanto para migraciones como runtime; así se evitan problemas con PgBouncer en transaction mode.
5. **Rate limit efectivo de Go:** con ~1.350 req/5h del modelo SQL, el límite práctico es ~600+ consultas/5h — de sobra para demos y sustentación.
