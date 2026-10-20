## Stack

Monorepo, dos despliegues independientes:

- `backend/` — Django 6 + DRF, arquitectura hexagonal por capas. Auth Supabase (JWT RS256 / JWKS).
- `frontend/` — Vite + JavaScript vanilla + Tailwind + Chart.js. **No hay React.** Las tres páginas son HTML separadas.

## Comandos

Backend (desde `backend/`):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt   # dev incluye pytest; requirements.txt no
cp .env.example .env                  # obligatorio: SECRET_KEY no tiene default
python manage.py migrate
python manage.py runserver            # http://127.0.0.1:8000/api/v1/
python -m pytest                      # suite completa
python -m pytest apps/tests/domain/test_domain_rules.py -q   # un archivo
```

Frontend (desde `frontend/`):

```bash
npm install
npm run dev    # http://localhost:5173, proxy /api → localhost:8000
npm test       # vitest (environment: node, sin DOM)
npm run lint
npx vitest run src/shared/eventBus.test.js   # un archivo
```

Stack completo: `docker compose up --build` → frontend en `:3000` (nginx), backend en `:8000`. Requiere `backend/.env` antes de arrancar.

**No hay CI** (`.github/` no existe): nada corre automáticamente. Ejecuta `npm run lint` y `python -m pytest` a mano antes de commitear.

## Backend: capas y regla de dependencia

Cada app usa `backend/apps/<app>/{domain,application,infrastructure,interfaces}/` con la regla:

```
interfaces → application → domain ← infrastructure
```

- El **composition root** es `backend/config/composition.py`. Construye adaptadores e inyecta puertos; `config/urls.py` consume `build_interface_urlpatterns()`. Cada `interfaces/urls.py` expone una factory `create_urlpatterns(use_cases)`. Un endpoint nuevo se registra ahí, no con estado global a nivel de módulo.
- **`apps/<app>/models.py` es una fachada** que re-exporta desde `infrastructure/models.py`. Edita el modelo en `infrastructure/`. Igual con `views.py`, `serializers.py`, `urls.py` y `repositories.py` en la raíz de cada app: son shims de compatibilidad, no la implementación.
- `backend/services/{ai,analysis}/` son puentes legacy que delegan en `apps/queries/application` e `apps/queries/infrastructure`. No añadas lógica ahí.
- Flujo obligatorio para features: `.opencode/agents/orchestrator.md` y el comando `/backend` — domain-architect → use-case-builder → infra-adapter → api-builder → test-engineer → architecture-reviewer.
- Los tests nuevos por capa viven en `backend/apps/tests/{domain,application,infrastructure,interfaces}/`.

## Backend: trampas

- **Los tests nunca tocan la BD del `.env`.** Bajo pytest, `settings.py` lee `CBI_TEST_DATABASE_URL`; sin ella cae a SQLite local. Los tests que requieren Postgres real se saltan con el marker `requires_postgres` (`conftest.py`). Nunca apuntes esas vars a Supabase.
- `SECRET_KEY` no tiene default: cualquier `manage.py`/`pytest` falla sin `backend/.env`.
- Auth es **solo Supabase**: `DEFAULT_AUTHENTICATION_CLASSES = apps.users.infrastructure.authentication.SupabaseAuth`. No hay SimpleJWT.
- **Modo demo es un camino de primera clase**: con header `X-Session-ID` se salta la auth (`IsAuthenticatedOrDemo`, `apps/core/interfaces/identity.py`). En vistas usa `request_identity(request, use_cases)`, nunca `request.user.pk` directo.
- Los datos de cada dataset viven en un **schema Postgres `ds_<dataset_id>`**, una tabla por hoja. `Dataset.db_path` guarda el **nombre del schema**, no una ruta de archivo. Las consultas usan conexión read-only (`DATABASE_READER_URL`, rol `bi_reader`) con `search_path` fijado.
- En Supabase usa el pooler en **puerto 5432** (session mode). El 6543 (transaction mode) rompe migraciones.
- Paginación global `PAGE_SIZE=20`: los endpoints de lista devuelven `{count, results}`. El frontend maneja ambos formatos.
- La caché es `LocMemCache` (por proceso), limpiada por un fixture autouse. No asumas Redis.
- El LLM es cualquier endpoint OpenAI-compatible (`LLM_*`). Sin `LLM_API_KEY` la app arranca, pero las consultas fallan.

## Frontend: trampas

- **Multi-página, no SPA.** Tres entrypoints en `vite.config.js`: `index.html` (landing), `pages/app.html` (consola), `pages/roadmap.html`. No hay router. `vite.html.js` aplana `pages/*.html` a la raíz de `dist/` y resuelve los `<!-- @include: ... -->` de `src/interfaces/views/`.
- **Capas hexagonales:** `src/domain/` (estado y puerto de charts), `src/application/` (casos de uso), `src/infrastructure/` (API, Supabase, chart.js), `src/interfaces/` (páginas, componentes, renderers, animaciones, vistas HTML) y `src/shared/` (eventBus, config, utilidades).
- Estado global mutable en `src/domain/state.js` + `src/shared/eventBus.js`. Varios módulos **se auto-suscriben al importarse** (`history.js`, `report.js`): importar un módulo tiene efectos secundarios.
- `src/infrastructure/api.js` es el único cliente HTTP. Añade `Authorization: Bearer <JWT de Supabase>` o `X-Session-ID` en demo. `API_BASE_URL` cae a `/api/v1` (proxy same-origin). Ojo: `api.js` importa `application/session.js`, violación de capas conocida.
- Vitest corre con `environment: 'node'`: **no hay DOM en tests**. Protege el acceso a `window`/`document` (ver `application/session.js`). La cobertura mide `src/infrastructure/charts/**` y `src/domain/charts/**`.
- Charts: `ChartRegistry` + 8 subclases de `ChartBuilder` son la capa puertos/adaptadores, con test cada una. Añade un tipo de gráfico registrando un builder, no ramificando en el render.
- `dist/` y `node_modules/` están gitignored. No commitees artefactos de build.

## Deploy

- Backend: blueprint `render.yaml` (rootDir `backend`, gunicorn, health `/api/v1/health/`).
- Frontend: Vercel con rootDir `frontend` y framework Vite. Las `VITE_*` se hornean en build time: cambiarlas exige redeploy.
- Nginx del compose hace proxy `/api` → `django`, permite uploads de 55 MB y timeouts de 600 s (el LLM puede tardar minutos).

## Agent skills

### Issue tracker

GitHub Issues usando el CLI `gh`. Ver `docs/agents/issue-tracker.md`.

### Domain docs

Layout de contexto único (`CONTEXT.md` + `docs/adr/` en la raíz). Ver `docs/agents/domain.md`. Ninguno de los dos existe todavía: el documento indica proceder en silencio, sin proponer crearlos.
