# ConversationalBI

> Hazle preguntas en lenguaje natural a tus datos. La IA genera SQL, ejecuta análisis y responde con gráficas y recibo SQL.

**Web en producción:**
- Frontend: [https://conversational-bi-eight.vercel.app/](https://conversational-bi-eight.vercel.app/)
- API: [https://conversationalbi-api.onrender.com/api/v1/health/](https://conversationalbi-api.onrender.com/api/v1/health/)

---

## Qué es

ConversationalBI es una aplicación de **Business Intelligence conversacional**:

1. Subes un CSV o Excel.
2. El sistema detecta el schema y materializa las tablas en Postgres.
3. Le haces preguntas en español (p. ej. *"¿cuáles son las 5 categorías con más ingresos?"*).
4. La IA genera SQL, lo ejecuta de forma segura con un rol de solo lectura y responde con un resumen en lenguaje natural + una gráfica + el SQL utilizado.

Proyecto orientado a un **Trabajo de Fin de Grado (TFG)** — migración de un stack local (Ollama + SQLite) a un stack cloud moderno (Render + Vercel + Supabase + OpenCode Go) con app nativa iOS en SwiftUI.

---

## Arquitectura

```
                    Web (Vite + Chart.js) ─┐
                                            │
                    iOS (SwiftUI + Swift Charts) ─┤
                                                    │
                    ┌───────────────────────────────┘
                    │
            Supabase Auth ── JWT
                    │
            ┌───────▼───────┐
            │  Django API     │  (Render)
            │  + LLMClient    │
            └───────┬───────┘
                    │
            ┌───────▼───────┐
            │  Supabase     │
            │  Postgres     │
            │  - schema public (app)
            │  - schemas ds_{id} (datasets)
            └───────────────┘
                    │
                    ▼
            OpenCode Go API
        kimi-k2.7-code  → SQL
        mimo-v2.5       → respuesta
```

---

## Stack tecnológico

| Capa | Tecnología |
|------|------------|
| **Backend** | Django 6 + Django REST Framework |
| **Base de datos** | Supabase Postgres |
| **LLM** | OpenCode Go API (OpenAI-compatible) |
| **Auth** | Supabase Auth (JWT RS256 validado en Django) |
| **Frontend** | Vite + JavaScript vanilla + Tailwind CSS + Chart.js |
| **App móvil** | SwiftUI + Swift Charts |
| **Deploy** | Render (API) + Vercel (frontend) |
| **Tests** | pytest (135 verdes + 22 skips por defecto) |

---

## Características principales

- **Upload de datos**: CSV/Excel con detección automática de schema, tipos y muestras.
- **Materialización segura**: cada dataset se guarda en un schema Postgres propio (`ds_{id}`).
- **SQL generado por IA**: el modelo `kimi-k2.7-code` escribe la consulta a partir de la pregunta en español.
- **Ejecución read-only**: las consultas corren bajo un rol Postgres `bi_reader` sin permisos de escritura.
- **Respuesta conversacional**: el modelo `mimo-v2.5` responde en lenguaje natural con resumen, sugerencias y SQL.
- **Gráficas interactivas**: Chart.js en la web, Swift Charts en iOS.
- **Historial de conversaciones**: cada dataset mantiene su historial de preguntas y respuestas.
- **Caché de consultas**: evita llamadas repetidas al LLM.
- **Cliente LLM agnóstico**: cambiar de proveedor (OpenCode Go, Groq, OpenRouter, Ollama) = cambiar env vars, no código.

---

## Estructura del proyecto

```
conversationalBI/
├── backend/
│   ├── apps/
│   │   ├── dataset/          # Upload, materialización, schemas
│   │   ├── queries/          # Chat, historial, caché, respuestas
│   │   └── users/            # Auth, perfil
│   ├── config/               # Settings, urls, wsgi/asgi
│   ├── services/
│   │   ├── ai/               # LLMClient, SQL agent, answer writer, prompts
│   │   └── analysis/         # Lectura de datasets, metadata
│   └── requirements.txt
├── frontend/                 # Vite + JS + Tailwind + Chart.js
├── samples/                  # CSVs de ejemplo
├── PLAN_MIGRACION.md        # Plan detallado de migración a cloud
├── FASE_4_SUPABASE_AUTH.md  # Guía de migración de auth
├── render.yaml              # Blueprint de Render
└── docker-compose.yml        # Stack local legacy
```

---

## Cómo correr localmente

### Requisitos

- Python 3.12
- Node.js 18+
- Cuenta en Supabase (para BD)
- API key de OpenCode Go (o LLM local)

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copiar y completar variables de entorno
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

La API queda en `http://127.0.0.1:8000/api/v1/`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

La web queda en `http://localhost:5173`.

### 3. Tests

```bash
cd backend
source .venv/bin/activate
python -m pytest
```

Por defecto: **135 tests pasan** y **22 se saltan** (los que requieren Postgres se ejecutan solo si configuras `CBI_TEST_DATABASE_URL` y `CBI_TEST_DATABASE_READER_URL`).

---

## Variables de entorno

### Backend (`backend/.env`)

```bash
# Django
SECRET_KEY=change-me-in-production
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173

# Postgres — usar pooler de Supabase en puerto 5432 (session mode)
DATABASE_URL=postgresql://postgres.<ref>:<pass>@aws-0-<region>.pooler.supabase.com:5432/postgres
DATABASE_READER_URL=postgresql://bi_reader.<ref>:<pass>@aws-0-<region>.pooler.supabase.com:5432/postgres
DATABASE_READER_ROLE=bi_reader

# Supabase (backend solo necesita la URL para JWKS)
SUPABASE_URL=https://xxxx.supabase.co

# LLM
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://opencode.ai/zen/go/v1
LLM_SQL_MODEL=kimi-k2.7-code
LLM_ANSWER_MODEL=mimo-v2.5
LLM_TIMEOUT=60
```

### Frontend (`frontend/.env`)

```bash
VITE_API_URL=http://localhost:8000/api/v1
VITE_SUPABASE_URL=https://xxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...
```

---

## API endpoints

### Auth

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/api/v1/users/register/` | Registro (legacy; desaparece en Fase 4) |
| `POST` | `/api/v1/users/login/` | Login (legacy; desaparece en Fase 4) |
| `POST` | `/api/v1/users/logout/` | Logout (legacy; desaparece en Fase 4) |
| `GET/POST/PATCH` | `/api/v1/users/profile/` | Perfil del usuario autenticado |

### Datasets

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/api/v1/dataset/` | Listar mis datasets |
| `POST` | `/api/v1/dataset/` | Subir CSV/Excel |
| `GET` | `/api/v1/dataset/{id}/` | Detalle del dataset |
| `GET` | `/api/v1/dataset/{id}/schema/` | Schema detectado |
| `DELETE` | `/api/v1/dataset/{id}/` | Eliminar dataset |

### Consultas

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/api/v1/queries/` | Preguntar en lenguaje natural |
| `GET` | `/api/v1/queries/` | Historial de consultas |
| `GET` | `/api/v1/queries/{id}/` | Detalle de una consulta |

### Health

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/api/v1/health/` | Ping para monitoreo |

---

## Deploy

### Render (backend)

1. En [dashboard.render.com](https://dashboard.render.com): **New → Blueprint**.
2. Conecta el repo `xofranc/conversationalBI`.
3. Render detecta `render.yaml` y crea el servicio.
4. Completa los secretos: `DATABASE_URL`, `DATABASE_READER_URL`, `LLM_API_KEY`.

### Vercel (frontend)

1. En [vercel.com](https://vercel.com): **Add New → Project**.
2. Importa el mismo repo.
3. **Root Directory**: `frontend`.
4. Framework: Vite.
5. Añade las env vars: `VITE_API_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`.

### Anti cold-start

Render Free duerme tras inactividad. Configura un cron en [cron-job.org](https://cron-job.org) que haga `GET` a `/api/v1/health/` cada 10 minutos.

---

## Roadmap de migración

| Fase | Descripción | Estado |
|------|-------------|--------|
| **0** | Setup de cuentas (OpenCode Go, Supabase) | ✅ |
| **1** | Migrar LLM: Ollama → OpenCode Go (`LLMClient`) | ✅ |
| **2** | Migrar BD: SQLite → Supabase Postgres (schema por dataset) | ✅ |
| **3** | Deploy web: Render + Vercel + cron + CORS | ✅ |
| **4** | Migrar auth: DRF SimpleJWT → Supabase Auth | ✅ |
| **5** | App iOS nativa (SwiftUI + Swift Charts) | ❌ |
| **6** | Hardening: Supabase Storage, dominio propio, monitoreo | ❌ |

Ver detalles en [`PLAN_MIGRACION.md`](PLAN_MIGRACION.md) y [`FASE_4_SUPABASE_AUTH.md`](FASE_4_SUPABASE_AUTH.md).

---

## App iOS (Fase 5)

La app iOS se conectará a la misma API Django en Render y usará Supabase Auth para el login (compartiendo sesión con la web). Verá la guía de aprendizaje de Swift/SwiftUI en `FASE_4_SUPABASE_AUTH.md` y el plan de implementación en `PLAN_MIGRACION.md`.

---

## Costos estimados

| Servicio | Costo | Límite |
|----------|-------|--------|
| OpenCode Go | $10/mes | ~$60/mes ≈ 20.000 consultas |
| Supabase | $0 | 500 MB DB, 50k MAU auth |
| Render + Vercel | $0 | Planes free |
| Apple Developer | $0 | No necesario (simulador) |

---

## Notas de seguridad

- Las consultas SQL se ejecutan con un rol Postgres **read-only** (`bi_reader`).
- El backend **nunca expone** el `SUPABASE_SERVICE_ROLE_KEY` ni el `LLM_API_KEY` al frontend.
- El `SECRET_KEY` de Django y el `LLM_API_KEY` se configuran como secretos en Render.
- El `DATABASE_URL` (rol de escritura) solo se usa para migraciones y materialización de datasets.

---

## Licencia

Este proyecto es un trabajo académico. Licencia por definir.

---

**Autor:** [xofranc](https://github.com/xofranc)
