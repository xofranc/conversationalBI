# Auditoría ConversationalBI

> **Fecha:** 23/07/2026 · **Actualizada:** 24/07/2026 (P0 + P1-backend + P2 + P3 resueltos — plan completado; ver [Historial](#10-historial))
> **Stack:** Django 6.0 + DRF + SimpleJWT + Ollama + SQLite + Pandas · Vite + Vanilla JS + Tailwind (CDN) · Docker Compose
> **Alcance:** Backend (`users`, `queries`, `dataset`, `services/ai`, `config`) + Frontend + Infra
> **Método:** revisión línea por línea + verificación dinámica (`manage.py check`, `makemigrations --check`, ejecución de la suite de tests, introspección de firmas)

---

## Índice

- [1. Resumen ejecutivo](#1-resumen-ejecutivo)
- [2. Backend — app `users`](#2-backend--app-users)
- [3. Backend — app `queries`](#3-backend--app-queries)
- [4. Backend — app `dataset`](#4-backend--app-dataset)
- [5. Backend — motor IA (`services/ai`)](#5-backend--motor-ia-servicesai)
- [6. Config (`settings.py`, `pytest.ini`, `.gitignore`)](#6-config-settingspy-pytestini-gitignore)
- [7. Frontend](#7-frontend)
- [8. Infra (`docker-compose.yml`)](#8-infra-docker-composeyml)
- [9. Plan de acción priorizado](#9-plan-de-acción-priorizado)
- [10. Historial](#10-historial)

---

## 1. Resumen ejecutivo

**Veredicto:** arquitectura en capas sólida y buenas decisiones de seguridad estructural (sandbox SQLite efímero, deny-by-default, JWT con blacklist), pero con **4 bugs críticos (P0)**, uno de los cuales **rompe por completo el endpoint de upload sin que los tests lo detecten**. La infraestructura Docker es actualmente **no funcional** y el frontend es una maqueta desconectada del backend real.

### Los 4 P0 que bloquean el proyecto hoy — **RESUELTOS (24/07/2026)**

| # | Hallazgo | Ubicación | Estado |
|---|---|---|---|
| P0-1 | `mark_ready` llamado con 3 args, definido con 2 → **todo upload termina en 500** y el dataset queda en `error` aunque el procesamiento fue correcto | `dataset/services/dataset_service.py:47` vs `dataset/models.py:58` | ✅ Firma unificada (`column_count` con default) + test de integración real |
| P0-2 | Suite de tests no arranca (`DJANGO_SETTINGS_MODULE` y `testpaths` inválidos) | `pytest.ini:2,7` | ✅ `config.settings` + `testpaths = apps services` |
| P0-3 | `.env` **no** está en `.gitignore` → la `SECRET_KEY` real está a un `git add -A` de commitearse | `backend/.gitignore` | ✅ `.env` añadido |
| P0-4 | `phone_number` unique + blank sin `null=True` → el segundo perfil sin teléfono lanza `IntegrityError` (500) | `users/models.py:80` | ✅ `null=True, blank=True` + migración |

### Lo mejor / lo peor por componente

| Componente | ✅ Lo mejor | ❌ Lo peor |
|---|---|---|
| `users` | Manager custom, `F()` atómico, throttling en auth | `phone_number` unique+blank, sin endpoint de refresh, código muerto masivo, 0 tests |
| `queries` | Capas limpias, índices compuestos, caché determinista | Fuga de errores internos, race condition en feedback, caché que corrompe métricas |
| `dataset` | Máquina de estados, FileService anti path-traversal | **Upload 100% roto** (P0-1), test roto con `user = ...`, prints de debug |
| Motor IA | **Sandbox SQLite efímero** (la joya), Ollama local, `temperature=0` | Sin timeouts ni límites de recursos, prompt de corrección sin `{question}`, NaN/Timestamp rompe `JSONField` |
| Config | Secrets por entorno, CORS whitelist, deny-by-default | `.env` no ignorado, `pytest.ini` no arranca la suite |
| Frontend | XSS impecable, Chart.js sin memory leaks | MOCK MODE desconecta todo, refresh token descartado, Tailwind por CDN |
| Infra | Volúmenes nombrados, imágenes pineadas | **No arranca**: rutas rotas, sin Dockerfiles, worker inexistente, Postgres/Redis huérfanos |

---

## 2. Backend — app `users`

### ✅ Lo mejor

- `CustomUserManager` correcto con `email` como `USERNAME_FIELD`, validación de superusuario y `normalize_email` (`models.py:8-33`).
- `AuthService.register` usa `Profile.objects.get_or_create` (idempotente) y separa bien validación (serializer) de negocio (servicio) (`services/auth_service.py:11-31`).
- `UserService.increment_usage` usa `F()` expressions → incremento atómico sin race condition (`services/user_service.py:32-35`).
- `LogoutSerializer` captura `TokenError` específico y usa `logger` (`serializers/auth.py:74-80`).
- Throttling en login/register (`views/auth.py:18,39`) y `permission_classes = []` explícito para sobreescribir el `IsAuthenticated` global.
- Admin de `User` bien adaptado al modelo sin username (`admin.py:5-19`).

### ❌ Lo peor

- **Código muerto masivo y lógica duplicada:** `AuthService.login`, `logout`, `change_password`, `deactivate_user`, `get_user_by_email` (`services/auth_service.py:35-102`) nunca se llaman; `LoginSerializer.validate` (`serializers/auth.py:40-59`) reimplementa la autenticación y devuelve menos campos que el servicio → inconsistencia de API.
- `RegisterSerializer.create` (`serializers/auth.py:24-31`) también es código muerto: la vista llama a `AuthService.register` directamente.
- **La cuota está desactivada:** el guard `can_query` está comentado en `queries/views.py:39-46`, pero `increment_usage` sí se ejecuta → se acumula `query_count` que nunca se valida.
- `ProfileSerializer` no tiene vista asociada → el perfil no es accesible por API (dead code).
- `UserService.increment_usage` traga cualquier excepción con `except Exception: pass` (`services/user_service.py:36-38`) — oculta errores reales de BD.
- `hasattr(profile, 'query_count')` (`user_service.py:20-22`) es defensa muerta: los campos existen desde la migración 0002.
- Validación de teléfono en `Profile.save()` (`models.py:89-97`) lanza `ValueError` → 500 en vez de 400; duplicada con `ProfileSerializer.validate_phone_number`. La validación pertenece al serializer, no al `save()`.

### 🐛 Bugs concretos

1. **`models.py:80`** — `phone_number = models.CharField(max_length=10, blank=True, unique=True)` sin `null=True`: en BD se guarda `''`, así que el **segundo perfil con teléfono vacío lanza `IntegrityError` (500)**. **P0**.
2. **`services/__init__.py:1-4`** — importa `AuthService` pero `__all__ = ['UserService']`: exportación inconsistente.
3. **`urls.py`** — falta `TokenRefreshView`: con el default de simplejwt (access token de 5 min) y sin refresh, el usuario debe re-loguearse cada 5 minutos.
4. **`serializers/auth.py:42-48`** — `LoginSerializer` no distingue cuenta desactivada (el check `is_active` existe solo en el `AuthService.login` muerto).
5. **`auth_service.py:18-21`** — TOCTOU: `filter(email).exists()` + `create_user` no es atómico; en concurrencia → `IntegrityError` 500. Debe confiar en la constraint única y capturar `IntegrityError`.
6. **Migraciones ruidosas:** `0001_initial.py:32` crea `user_type_id` y `0003` lo elimina — candidato a squash (consistencia actual verificada OK).
7. **Sin tests**: `apps/users/` no tiene directorio de tests (0% cobertura en auth/registro).

### Mejoras priorizadas

- **P0:** `phone_number` → `null=True, blank=True` (+ migración) o quitar `unique`.
- **P1:** Añadir `path('token/refresh/', TokenRefreshView.as_view())`; decidir la cuota (activar el guard o eliminar `query_count`); eliminar código muerto y unificar login en `AuthService`.
- **P2:** Mover validación de teléfono fuera de `save()`; quitar `except: pass` de `increment_usage`; exponer endpoint de perfil con `ProfileSerializer`.
- **P3:** Tests de registro/login/logout/refresh; squash de migraciones 0001-0003.

---

## 3. Backend — app `queries`

### ✅ Lo mejor

- Arquitectura en capas limpia: vista → `QueryService` → `AIQueryService` (el motor AI no conoce Django) → `QueryRepository`.
- Índices compuestos bien pensados en `QueryHistory` (`user,created_at`, `dataset,success`, `user,success`) (`models/queryHistory.py:43-47`).
- `select_related('result')` en `get_queryset` (`views.py:21-23`) → evita N+1 en historial.
- Métricas del TFG modeladas en el propio modelo (`model_used`, `retry_count`, `cached`).
- Separación de `QueryResult` y `QueryFeedback` con OneToOne — normalización correcta.
- `CacheService` con clave determinista (md5 de pregunta normalizada + dataset) (`services/cache_service.py:10-13`).

### ❌ Lo peor

- **Fuga de errores internos:** `views.py:56-60` devuelve `{'error': str(e)}` con 500 — expone trazas de Ollama/SQLite/pandas al cliente.
- **Race condition en feedback:** `views.py:97-110` hace check `hasattr(query, 'feedback')` y luego `create()` → dos requests concurrentes pasan el check y el segundo explota con `IntegrityError` (500).
- **El caché corrompe las métricas:** un hit de caché (`query_service.py:24-27`) no persiste ningún `QueryHistory` → las consultas cacheadas desaparecen del historial y de las métricas del TFG; además devuelve el `query_id` de la consulta original, por lo que un feedback sobre una respuesta cacheada se ancla a la query de otro momento. Y `cached['cached'] = True` muta el objeto cacheado en sitio (con LocMemCache es la misma referencia).
- **No se valida que el dataset esté `READY`:** ni `can_access_dataset` ni `QueryService.execute` chequean `status` → se puede consultar un dataset en `error`/`processing` con `schema_json={}`.
- **Filtro "anti-SQL-injection" en la pregunta** (`serializers/query_request.py:16-25`): capa equivocada, falsos positivos garantizados ("show the drop in sales"), y redundante con `SQLValidator`. Seguridad de teatro que degrada UX.
- `QueryHistorySerializer` incluye `result_json` completo **también en el listado** → hasta 1000 filas × 20 por página = payloads enormes.
- `repositories.py:50-60` (`get_history`, `get_by_id`) es código muerto: las vistas hacen sus propias queries.
- `views.py:17` — `CreateModelMixin` innecesario: `create()` está sobrescrito por completo.
- Import local dentro del método (`query_service.py:63`) — síntoma de mala organización de dependencias.
- `CharType` es typo de `ChartType` (`models/queryHistory.py:7`).

### 🐛 Bugs concretos

1. **`views.py:58`** — info disclosure de excepciones internas al cliente.
2. **`views.py:97-110`** — race condition check-then-act en feedback (IntegrityError 500).
3. **`services/query_service.py:24-27`** — hit de caché no persiste historial ni incrementa cuota: contabilidad inconsistente.
4. **`serializers/query_response.py`** — list endpoint serializa `result` completo (riesgo de rendimiento).
5. **`services/query_service.py:30`** — `DatasetRepository.get_schema` lanza `DoesNotExist` si el dataset no existe → cae en el `except Exception` → 500 en vez de 404.
6. **Sin tests**: `apps/queries/` no tiene tests (0% sobre el endpoint más crítico del producto).

### Mejoras priorizadas

- **P0:** Validar `dataset.status == READY` antes de ejecutar; mapear `DoesNotExist` → 404; sanitizar el mensaje de error al cliente.
- **P1:** Persistir `QueryHistory` también en hits de caché (con `cached=True`); arreglar race de feedback con `IntegrityError`→400; decidir el guard de cuota.
- **P2:** Serializer ligero para `list` (sin `result_json`); eliminar el blacklist de palabras de la pregunta; quitar mixin y métodos de repositorio muertos.
- **P3:** Renombrar `CharType`→`ChartType` (con migración de choices); tests de create/list/retrieve/feedback y del flujo de caché.

---

## 4. Backend — app `dataset`

### ✅ Lo mejor

- Máquina de estados explícita (`Status` TextChoices) con transiciones dedicadas `mark_ready`/`mark_error` usando `update_fields` (`models.py:58-69`).
- Separación de responsabilidades ejemplar: `DatasetService` orquesta, `FileService` archivos, `SchemaService` pandas.
- `FileService.save` usa nombres UUID + extensión whitelist → sin path traversal; escritura por chunks (`file_service.py:24-41`).
- Permiso de objeto `IsDatasetOwner` aplicado por acción vía `get_permissions` dinámico (`views.py:48-51`, `permissions.py`).
- Serializers separados list/detail/upload; el list excluye `schema_json` y tablas.
- `_safe_sample` convierte numpy/datetime a tipos JSON-seguros (`schema_service.py:70-82`) — detalle de calidad.

### ❌ Lo peor

- **BUG CRÍTICO P0** — ver detalle abajo.
- **Prints de debug en producción:** `dataset_service.py:19-21,39`, `serializers/datasetUpload.py:24-26`, `file_service.py:16` — fugan metadatos de archivos a stdout/logs.
- `views.py:71-75` — `'Error al procesar el archivo.' + str(e)`: fuga de error interno + concatenación sin espacio.
- **Validación duplicada con constantes divergentes:** extensiones y tamaño máximo definidos dos veces (`datasetUpload.py:13,40` y `file_service.py:6-7`) — el serializer valida `content_type` (trivialmente falsificable) y el servicio no.
- `SchemaService.extract` (`schema_service.py:12-19`): el docstring dice "recibe ruta relativa" pero `dataset_service.py:38-40` le pasa una **absoluta** y `extract` vuelve a hacer `os.path.join(MEDIA_ROOT, ...)` — funciona por accidente. Frágil y contradictorio.
- `list()` sin paginación (`views.py:83-86`) aunque settings define `PageNumberPagination`; `get_queryset` hace `prefetch_related('tables')` también para el list, que no usa tablas → query desperdiciada.
- Archivo huérfano cuando falla la extracción de schema: el archivo ya se guardó y nunca se borra al hacer `mark_error`.
- `admin.py` vacío — `Dataset`/`DatasetTable` no registrados (inconsistente con users/queries).
- `_infer_dtype` con `pd.to_datetime` heurístico (`schema_service.py:91-95`) clasifica cadenas como `'2024'` como fecha (falso positivo).

### 🐛 Bugs concretos

1. **`services/dataset_service.py:47` vs `models.py:58`** — se llama `mark_ready(schema, row_count, col_count)` con **3 argumentos**, pero el modelo define `mark_ready(self, schema, row_count)` con **2**. Verificado por introspección: `TypeError: mark_ready() takes 3 positional arguments but 4 were given`. Consecuencia: **TODO upload exitoso termina en excepción → `mark_error` → HTTP 500 → el dataset queda en estado `error` aunque el procesamiento fue correcto, y `column_count` nunca se persiste.** El endpoint de upload está completamente roto. El test `test_upload_exitoso` no lo detecta porque mockea `DatasetService.create` (`tests/test_views.py:73`). **P0**.
2. **`tests/test_dataset_service.py:14`** — `user = ...` (Ellipsis literal): el test falla con `Cannot assign "Ellipsis"`. Verificado: **1 failed, 15 passed**.
3. **`schema_service.py:18`** — doble join de MEDIA_ROOT (contrato de ruta roto/ambiguo).
4. **`services/ai/sql_executor.py:60-66`** (contrato directo) — `pd.read_json` **nunca retorna `dict`**: la rama multi-tabla JSON es código muerto; un JSON multi-tabla se esquematiza como N tablas pero se ejecuta como una sola tabla malformada → el SQL generado referencia tablas inexistentes.
5. **`sql_executor.py:22-23`** — `'limit' not in sql.lower()`: substring naive (una columna `limit_amount` impide añadir el LIMIT).
6. **`DatasetRepository.get_schema` (`repositories.py:29-31`)** no filtra por `status`.

### Mejoras priorizadas

- **P0:** Corregir la firma (añadir `column_count` a `mark_ready` o quitar el argumento) y escribir un test de integración real de upload sin mocks.
- **P1:** Eliminar prints; sanitizar errores al cliente; unificar constantes de validación en un solo módulo; borrar el archivo cuando el procesamiento falla.
- **P2:** Arreglar `test_dataset_service.py` (fixture real); aclarar el contrato relativo/absoluto de `SchemaService.extract`; paginar `list`; prefetch solo en `retrieve`.
- **P3:** Registrar modelos en admin; afinar `_infer_dtype` (exigir separadores de fecha); corregir la carga de JSON multi-tabla en `sql_executor`.

---

## 5. Backend — motor IA (`services/ai`)

### ✅ Lo mejor

- **El sandbox es la joya del diseño:** `SQLExecutor` carga el dataset en un **SQLite en memoria, efímero y por consulta** (`sql_executor.py:54`), que contiene *únicamente* las tablas del propio dataset. Aunque el validador fallara, el blast radius está contenido: no hay BD real que alterar. Defensa en profundidad real.
- Pipeline desacoplado y unidireccional: `PromptBuilder` → `SQLAgent` → `SQLValidator` → `SQLExecutor` → `ChartSelector`, orquestado por `AIQueryService`. Cada clase tiene una única responsabilidad y es testeable de forma aislada.
- Validador en dos capas: patrones bloqueados + verificación estructural con `sqlparse` de que el primer token sea `SELECT` (`sql_validator.py:25-56`); multi-statement bloqueado vía `;`.
- Sin fugas de API keys: **Ollama local** (`sql_agent.py:8-12`), host y modelo por variables de entorno. Los datos no salen de la máquina. Decisión de privacidad acertada.
- `temperature = 0` para SQL determinista (`sql_agent.py:11`).
- `_clean()` elimina fences markdown del LLM (`sql_agent.py:18-28`) — problema real y frecuente, bien resuelto.
- Bucle de autocorrección acotado con `MAX_RETRIES = 3` (`ai_query_service.py:8,31-53`).
- `ChartSelector` determinista con fallback seguro a `'table'`; `conn.close()` en `finally` (`sql_executor.py:36-37`).

### ❌ Lo peor

**Rendimiento / disponibilidad (lo más grave)**

1. **Re-lectura completa del archivo en cada consulta** (`sql_executor.py:30,56-72`). Cada pregunta vuelve a parsear el CSV/Excel/JSON entero (hasta 50 MB) y a volcarlo a SQLite en memoria. Es el cuello de botella número uno del sistema.
2. **Sin timeout en la llamada al LLM** (`sql_agent.py:15`). Si Ollama se cuelga, el worker de Django queda bloqueado indefinidamente × 3 reintentos. DoS accidental trivial.
3. **Sin límites en la ejecución SQL**: ni `progress_handler`, ni timeout de query, ni límite de memoria. Un `CROSS JOIN` cartesiano puede inflar la RAM del proceso web hasta tumbarlo.
4. **El tope `MAX_ROWS` es eludible**: solo se añade `LIMIT 1000` si el texto no contiene la subcadena "limit"; el LLM puede generar `LIMIT 999999999` sin tope máximo forzado.

**Concurrencia y caché**

5. **Cache stampede**: `get` → ejecutar LLM → `set` sin locking (`query_service.py:24-69`). N requests concurrentes idénticos disparan N llamadas al LLM.
6. **Caché sin invalidación por cambio de dataset**: la clave es `md5(dataset_id:pregunta)`; si el archivo se reprocesa, se sirven resultados obsoletos durante 1 hora.
7. **`LocMemCache`**: no se comparte entre workers/procesos de gunicorn y se pierde al reiniciar.

**Manejo de errores y observabilidad**

8. **`except Exception` que captura también violaciones de seguridad** (`ai_query_service.py:45`): cuando el validador rechaza SQL peligroso, el sistema *reintenta* en lugar de fallar rápido. Gasta cuota de LLM y enmascara eventos de seguridad.
9. **Sin `logging` en ningún archivo del motor IA**: fallos del LLM, del validador y del executor desaparecen sin rastro.
10. **Persistencia no atómica**: `save_query` + `save_result` sin transacción (`query_service.py:40-60`). Si `save_result` falla, queda un `QueryHistory` con `success=True` huérfano de resultado.

**Integridad funcional**

11. **La cuota nunca se enforcea** pero `increment_usage` se ejecuta siempre — incluso cuando la consulta falla. Se cobra sin limitar.
12. **Prompt injection directa e indirecta sin mitigación específica**: la pregunta se interpola cruda (`prompt_builder.py:15`) y los *sample values* del dataset también (`prompt_builder.py:62`). El sandbox SQLite contiene el impacto, pero es la única barrera real.

### 🐛 Bugs concretos

| # | Sev. | Ubicación | Descripción |
|---|---|---|---|
| 1 | Alta | `prompt_builder.py:43-49` vs `19-33` | `build_correction()` recibe `question` pero `CORRECTION_TEMPLATE` **no contiene `{question}`**: el parámetro se descarta silenciosamente. El LLM corrige sin conocer la intención original. |
| 2 | Alta | `sql_executor.py:62-64` | `pd.read_json()` nunca retorna `dict` → la rama multi-tabla JSON jamás se ejecuta. **Schema prometido ≠ tablas cargadas** en SQLite. |
| 3 | Alta | `sql_executor.py:22` | `'limit' not in sql.strip().lower()` detecta **subcadena**, no keyword: una columna `limite_credito` suprime el LIMIT de seguridad. Debe ser regex `\blimit\b`. |
| 4 | Alta | `sql_executor.py:75-79` vs `schema_service.py:85-96` | **Inconsistencia de dtypes**: `_dtype()` no tiene la heurística de fechas que sí tiene `_infer_dtype()`. Una columna reportada como `date` vuelve como `str` → `ChartSelector.pick` nunca elige `'line'` para series temporales. Contrato roto con el frontend. |
| 5 | Alta | `sql_executor.py:43` → `repositories.py:40-47` | `df.to_dict(orient='records')` produce `NaN` y `pd.Timestamp`, que **no son JSON-serializables** al guardar en `QueryResult.result_json` (JSONField). `Timestamp` lanza `TypeError` → consultas con fechas explotan *después* de marcarse como exitosas. Falta normalización análoga a `_safe_sample`. |
| 6 | Media | `ai_query_service.py:42` vs `47` | **Semántica inconsistente de `retry_count`**: en éxito guarda `attempt` (0-based) pero en fallo guarda `attempt + 1` (= intentos, no reintentos). Métrica contaminada. |
| 7 | Media | `query_service.py:50` + `24-27` | **Campo `cached` muerto**: los hits de caché retornan sin persistir nada; todo `QueryHistory` se guarda con `cached=False`. Métrica perdida. |
| 8 | Media | `sql_executor.py:68-72` | Cualquier extensión que no sea `.csv`/`.json` cae al branch de Excel; un `.txt` produciría un error críptico. Falta `else: raise ValueError(...)`. |
| 9 | Media | `query_service.py:30` / `views.py:54-60` | `get_schema()` lanza `DoesNotExist` y no se verifica `status == READY`: un dataset en `PROCESSING`/`ERROR` tiene `schema_json={}` → prompt vacío, LLM alucina, error 500 con `str(e)` crudo. |
| 10 | Media | `sql_executor.py:26` | `os.path.join(MEDIA_ROOT, dataset.file_path)` sin normalizar ni verificar contención. Riesgo bajo hoy (uuid generado por servidor), pero es un path-traversal latente. |
| 11 | Baja | `sql_validator.py:9` | El patrón `r';'` bloquea `;` **dentro de strings literales** (`WHERE nota = 'a;b'`) → falso positivo. |
| 12 | Baja | `sql_validator.py:49-54` | Los **CTE (`WITH ... SELECT`) se rechazan** aunque sean SELECT puros — limitación no documentada que genera reintentos inútiles. |
| 13 | Baja | `sql_executor.py:23` | `sql.rstrip(";")` es dead code: el validador ya prohibió `;`. |
| 14 | Baja | `ai_query_service.py:35` | La comparación exacta `sql.strip() == 'NO_SQL_POSSIBLE'` falla si el modelo añade cualquier texto extra. |
| 15 | Baja | `cache_service.py:13` | `hashlib.md5` puede estar deshabilitado en entornos FIPS; usar `sha256`. No se normalizan espacios/unicode en la clave. |
| 16 | Baja | `prompt_builder.py:62-67` | Samples sin truncar longitud y schema sin límite de tamaño: un Excel de muchas hojas puede desbordar el contexto del modelo. |
| 17 | Baja | `prompt_builder.py:64` | `table['name']` con acceso directo → `KeyError` si el schema llega malformado. |
| 18 | Baja | `sql_agent.py:21-28` | `_clean` solo elimina fences; si el modelo antepone prosa, pasa íntegra al validador. Falta extracción del primer statement. |
| 19 | Info | `ai_query_service.py:13-16` vs `sql_executor.py:20,25` | El docstring presume "no toca la BD de la app", pero `SQLExecutor` importa `DatasetRepository` y sí consulta la BD. La frontera arquitectónica declarada no es real. |

### Mejoras priorizadas

**ALTA**

1. **Timeout en el LLM** (`sql_agent.py:8-15`): pasar `timeout` al cliente Ollama (p. ej. 60 s) y un presupuesto total en `AIQueryService.execute`.
2. **Límites duros en `SQLExecutor`**: envolver el SQL (`SELECT * FROM (<sql>) LIMIT 1000`), `conn.set_progress_handler()` para matar queries runaway, y `else` explícito para extensiones no soportadas.
3. **Corregir serialización de resultados** (`sql_executor.py:43`): normalizar `NaN → None`, `Timestamp → isoformat()` (reutilizar `_safe_sample`) antes de `to_dict`.
4. **Arreglar la rama JSON del ejecutor** (`sql_executor.py:60-67`): replicar `SchemaService._read_file` o, mejor, **compartir una única función de carga** entre ambos módulos.
5. **Unificar `_dtype` con `_infer_dtype`**: misma heurística de fechas en ambos lados.
6. **Incluir `{question}` en `CORRECTION_TEMPLATE`** (`prompt_builder.py:19-33`).
7. **No reintentar violaciones del validador** (`ai_query_service.py:45`): distinguir `SecurityError` (fail-fast + log) de errores de ejecución (reintentables). Añadir `logging` en todos los `except`.
8. **Detección de LIMIT por regex** (`sql_executor.py:22`): `re.search(r'\blimit\b', sql, re.I)`.

**MEDIA**

9. Caché de la base SQLite (o del DataFrame) por dataset con invalidación por `updated_at`/`file_size` — la mayor ganancia de rendimiento disponible.
10. Clave de caché con versión del dataset; migrar a Redis si hay múltiples workers; lock por clave (stampede).
11. Transacción en la persistencia (`transaction.atomic()` alrededor de `save_query` + `save_result`).
12. Enforcear cuota y registrar hits de caché como `QueryHistory(cached=True)`.
13. Sanitizar errores al cliente; verificar `dataset.status == READY` antes de ejecutar.
14. Anti path-traversal (`realpath` + prefijo `MEDIA_ROOT`); eliminar `except Exception: pass`.

**BAJA**

15. Extraer el primer statement real del output del LLM; `startswith('NO_SQL_POSSIBLE')`.
16. Soportar CTEs en el validador o documentar la restricción en el prompt.
17. Truncar samples por longitud; `.get('name', '?')`; homogeneizar `retry_count`; `sha256` para claves de caché.
18. Inyectar `SQLAgent` como dependencia para testabilidad; **añadir tests** (hoy no existe ninguno para `services/ai` ni `apps/queries`, siendo el módulo más crítico del sistema).

---

## 6. Config (`settings.py`, `pytest.ini`, `.gitignore`)

### ✅ Lo mejor

- `SECRET_KEY` y `DEBUG` desde entorno sin fallback inseguro (falla rápido si falta) (`settings.py:31-34`).
- `ALLOWED_HOSTS` y `CORS_ALLOWED_ORIGINS` por whitelist vía env — no se usa `CORS_ALLOW_ALL` (`settings.py:36,74-78`).
- `CorsMiddleware` en primera posición (`settings.py:64`).
- `DEFAULT_PERMISSION_CLASSES = IsAuthenticated` global (deny by default) + throttling global (`settings.py:156-171`).
- `rest_framework_simplejwt.token_blacklist` instalado → logout real con blacklist.
- `manage.py check` → 0 issues; `makemigrations --check --dry-run` → migraciones consistentes (verificado dinámicamente).

### ❌ Lo peor

- **`.env` NO está en `.gitignore`:** la sección "Secrets" lista `.venv`/`.venv.*` donde claramente debía decir `.env` (copy-paste fallido de la recomendación de la auditoría previa). Verificado con git: `.env` no está trackeado **ni ignorado** — un `git add -A` commitea la `SECRET_KEY` real que contiene. **P0**.
- **`pytest.ini` roto (verificado ejecutándolo):** línea 2 `DJANGO_SETTINGS_MODULE = backend.config.settings` (módulo inexistente — `backend/` no es paquete) y línea 7 `testpaths = backend/apps/dataset/tests/` (ruta inexistente desde `backend/`). Resultado: **la suite completa no arranca** (`ImportError: No module named 'backend'`). `conftest.py:8-9` parchea con `django.setup()` manual. **P0**.
- Throttle rate `'login': '10/hour'` (`settings.py:169`) sin ningún scoped throttle que lo use — config muerta.
- `LocMemCache` (`settings.py:175-179`): no compartida entre workers de gunicorn; las respuestas cacheadas desaparecen según el worker que atienda.
- Sin `SIMPLE_JWT` configurado: lifetimes por defecto (5 min access) sin endpoint de refresh publicado.
- Sin configuración de `LOGGING` pese al uso de `logger` en la app.
- `LANGUAGE_CODE = 'en-us'` (`settings.py:133`) con toda la app en español.
- Cabeceras de seguridad de producción ausentes (SECURE_SSL_REDIRECT, HSTS, etc.) — documentar para despliegue.
- Inconsistencia de naming `api/v1/dataset/` (singular) vs `users/` y `queries/`.

### Mejoras priorizadas

- **P0:** Añadir `.env` a `.gitignore` (y rotar la SECRET_KEY si alguna vez se expuso); arreglar `pytest.ini` → `DJANGO_SETTINGS_MODULE = config.settings`, `testpaths = apps`.
- **P1:** Publicar `TokenRefreshView` y definir `SIMPLE_JWT` (lifetimes, rotación); quitar el scope `login` muerto o implementarlo con `ScopedRateThrottle`.
- **P2:** Redis (o `FileBasedCache`) para caché compartida; configurar `LOGGING`.
- **P3:** `LANGUAGE_CODE = 'es-co'`; unificar naming de URLs; checklist de despliegue (`manage.py check --deploy`).

---

## 7. Frontend

### ✅ Lo mejor

- **Mitigación de XSS impecable:** todas las inyecciones dinámicas usan `innerText`/`textContent` y nodos creados con `createElement` (`main.js:176,228,323,339`). Los únicos `innerHTML` son asignaciones de string vacío para limpiar — inofensivos.
- **Gestión correcta de instancias Chart.js:** `main.js:241-242` destruye los charts previos antes de re-renderizar. Evita el memory leak clásico.
- **Capa API sólida:** borra `Content-Type` cuando el body es `FormData` (`api.js:31-33`), maneja 204, propaga errores estructurados `{status, data}`.
- **Parsing de errores DRF** coherente con lo que devuelve Django REST (`main.js:71,103-108`).
- Separación de concerns: animaciones en `animations.js`, red en `api.js`, estado en `main.js`. IDs del DOM consistentes contra `index.html` (verificados uno a uno).
- Flujo register→login correcto contra el contrato real del backend (`res.access` coincide con `LoginSerializer`).
- Tooling moderno (Vite + ESM); accesibilidad parcial: `lang="es"`, labels con `for`.

### ❌ Lo peor

- **El "MOCK MODE" anula todo el producto** (`main.js:10-27`): se oculta la vista de auth, se inyecta `currentDatasetId = 999` y datos hardcodeados. Todo el flujo de login/registro implementado es código muerto en la práctica. Contra el backend real (que exige JWT en todo) la app devolvería 401 en todo.
- **La API real nunca se llama para las dos funciones centrales:** `handleUpload` (`main.js:151-171`) simula la subida con `setTimeout(1500)` y jamás invoca `api.dataset.upload()`; `sendMessage` (`main.js:193-214`) jamás invoca `api.query.ask()`.
- **Manejo de tokens inseguro e incompleto:** access token en `localStorage` (exfiltrable vía XSS); el backend devuelve `access` + `refresh` pero el frontend **descarta el refresh**; el logout del backend exige el refresh para blacklist y el frontend solo borra el token local → el refresh queda válido para siempre. Contradicción total con `token_blacklist`.
- **Race conditions y loaders huérfanos:** tweens GSAP solapados sin `overwrite` ni `kill()`; `setTimeout` mock no cancelados (mensaje del "AI" aparece tras logout); `sendMessage` sin deshabilitar el botón ni debounce.
- **Tailwind por CDN en producción** (`index.html:13`): runtime JIT de desarrollo, desaconsejado explícitamente para producción (sin purga, ~100 KB de JS, FOUC). Y `package.json` ni siquiera declara `tailwindcss`.
- **`alert()` como sistema de errores** (`main.js:153,169,198`): bloqueante, no estilable, inaccesible.
- **Accesibilidad:** drop-zone sin `role="button"`/`tabindex`/teclado; botones-icono sin `aria-label`; `#chat-messages` sin `aria-live`; `text-light` es clase fantasma (no definida en la config); favicon `/vite.svg` inexistente → 404.
- **CSS problemático:** `align-self: flex-end` en `.chat-message` es código muerto; scrollbar solo WebKit (sin Firefox); variables CSS apenas usadas.
- **Chart.js sin tree-shaking:** `chart.js/auto` importa la librería entera (~200 KB).

### 🐛 Bugs concretos

| Ubicación | Bug |
|---|---|
| `src/main.js:17` | `currentDatasetId = 999` hardcodeado: contra el backend real sería 403. |
| `src/main.js:106` | `err.data[keys[0]][0]` rompe si el error DRF es string, no array (muestra solo el primer carácter). |
| `src/main.js:151-171` | `handleUpload` nunca llama a `api.dataset.upload()`; el `catch` es inalcanzable (try/catch sobre `setTimeout` síncrono). |
| `src/main.js:205-209` | Mismo patrón: `catch` jamás captura nada. |
| `src/main.js:194-195` | Permite mensajes de 1 carácter; el backend exige `min_length=5` → 400 si se conectara. |
| `src/api.js:3` | `API_BASE_URL` hardcodeada a `http://localhost:8000/api/v1` — sin `import.meta.env`; en producción apunta a localhost. |
| `src/api.js:66` | Upload envía solo `file`; falta `name` requerido por `DatasetUploadSerializer` → 400 garantizado si se conectara. Tampoco soporta `.json` (que el backend sí acepta). |
| `src/api.js:7-16` | Access token en `localStorage`; refresh descartado; `/users/logout/` jamás llamado. |
| `index.html:5` | `/vite.svg` inexistente → 404. |
| `index.html:37` | Clase `text-light` no definida en la config Tailwind. |
| `main.js:255,273,292` | `new Chart()` síncrono mientras el contenedor puede estar `hidden` → canvas a 0×0 (race condition latente). |

### Mejoras priorizadas

- **ALTA:** Eliminar MOCK MODE y cablear `handleUpload` → `api.dataset.upload()` (con campo `name`) y `sendMessage` → `api.query.ask()`; guardar `refresh` token, implementar flujo de refresh y llamar a `POST /users/logout/`; `API_BASE_URL` vía `import.meta.env.VITE_API_URL` + proxy en dev; Tailwind en el build de Vite en vez de CDN.
- **MEDIA:** `gsap.killTweensOf` en loader; cancelar `setTimeout` en logout; deshabilitar `send-btn` en vuelo; validar `min_length=5`; reemplazar `alert()` por toasts; tree-shake de Chart.js (~60% menos bundle); correcciones de accesibilidad.
- **BAJA:** ESLint + Prettier + tests (hoy sin tooling de calidad); limpiar CSS muerto; `scrollbar-width` para Firefox; favicon real en `public/`.

---

## 8. Infra (`docker-compose.yml`)

### ✅ Lo mejor

- Volúmenes nombrados para Postgres, Redis y modelos de Ollama — persistencia correcta.
- Imágenes pineadas a tags concretos (`postgres:16-alpine`, `redis:7-alpine`) en vez de `latest`.
- Intención arquitectónica correcta: web (gunicorn), worker de IA y LLM separados; Postgres y Redis **sin** puertos publicados al host.
- GPU de Ollama documentada aunque comentada.

### ❌ Lo peor — estado no funcional

- **El compose no puede arrancar: rutas de build rotas.** El archivo vive en `infra/` pero declara `build: ./frontend` y `build: ./backend` (líneas 6,11,18) → resuelven a `infra/frontend` e `infra/backend`, que **no existen**.
- **No existe ningún Dockerfile en todo el repositorio** → los tres servicios con `build:` fallan.
- **`env_file: .env` inexistente** (líneas 15,21): relativo a `infra/`; el `.env` real está en `backend/.env`. Compose aborta con "env file not found".
- **`langchain-worker` ejecuta un módulo que no existe**: `python -m services.ai.worker` (línea 19) → `ModuleNotFoundError` inmediato.
- **Servicios declarados pero no usados por el backend:**
  - **Postgres:** `settings.py:103-108` usa **SQLite**; `requirements.txt` no incluye `psycopg`. Servicio huérfano — con credenciales hardcodeadas `user/pass` versionadas en git (líneas 26-28).
  - **Redis:** caché real es `LocMemCache`; no hay `redis`/`django-redis` en requirements. Otro servicio huérfano.
- **`gunicorn` no está en `requirements.txt`** → el comando de la línea 12 falla dentro del contenedor.
- **Puerto de Ollama expuesto al host** (`11434:11434`): la API de Ollama no tiene autenticación.
- **Cero healthchecks:** `depends_on` solo espera "container started"; django y el worker arrancarán contra servicios no listos.
- **`.env.example` incompleto y con línea duplicada:** `OLLAMA_HOST` aparece dos veces; faltan `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `OLLAMA_MODEL`.
- **Frontend inviable en compose:** puerto 3000 pero Vite sirve en 5173/4173; URL de API hardcodeada a `localhost:8000` cuando en la red compose debería ser `http://django:8000`.
- Detalles: `version: "3.9"` obsoleto en Compose v2; sin `restart` policies; `pytest` mezclado en requirements de producción; sin volumen para `MEDIA_ROOT` (los uploads se pierden al recrear el contenedor).

### 🐛 Bugs concretos

| Ubicación | Bug |
|---|---|
| `docker-compose.yml:6,11,18` | Rutas `build:` relativas a `infra/` → directorios inexistentes. |
| `docker-compose.yml:15,21` | `env_file: .env` no existe en `infra/`. |
| `docker-compose.yml:19` | `python -m services.ai.worker` — módulo inexistente → crash. |
| `docker-compose.yml:12` + `requirements.txt` | `gunicorn` no instalado → comando falla. |
| `docker-compose.yml:23-29` vs `settings.py:103-108` | Postgres declarado; Django usa SQLite; sin `psycopg`. |
| `docker-compose.yml:31-33` vs `settings.py:175-179` | Redis declarado; caché real es LocMem; sin cliente redis. |
| `docker-compose.yml:28` | `POSTGRES_PASSWORD: pass` hardcodeada y versionada. |
| `docker-compose.yml:37` | Ollama publicado al host sin auth. |
| `.env.example:3-4` | `OLLAMA_HOST` duplicado; faltan `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `OLLAMA_MODEL`. |
| `requirements.txt:34-35` | `pytest`/`pytest-django` en dependencias de producción. |

### Mejoras priorizadas

- **ALTA:** Mover `docker-compose.yml` a la raíz (o corregir paths a `../...` y `env_file: ../backend/.env`) y crear los Dockerfiles; decidir la arquitectura real (conectar Postgres+Redis o eliminarlos); añadir `gunicorn` a requirements y mover `pytest*` a `requirements-dev.txt`; eliminar o implementar `services/ai/worker.py`; healthchecks + `depends_on: condition: service_healthy`.
- **MEDIA:** Credenciales a `.env`; `.env.example` completo sin duplicados; no publicar `11434` al host; `ollama pull` del modelo en el primer arranque; frontend con build multi-stage (Node → nginx) y URL de API parametrizada; eliminar `version: "3.9"`.
- **BAJA:** Perfiles de compose (`dev`/`prod`); límites de recursos para Ollama; volumen para `MEDIA_ROOT`.

---

## 9. Plan de acción priorizado

| Fase | Ítem | Componente | Estado (24/07/2026) |
|---|---|---|---|
| **P0 — Reparar lo roto** | 1. Firma de `mark_ready` (añadir `column_count` o quitar el arg) + test de integración real de upload | `dataset` | ✅ |
| | 2. `pytest.ini`: `DJANGO_SETTINGS_MODULE = config.settings`, `testpaths = apps` | `config` | ✅ |
| | 3. Añadir `.env` a `.gitignore`; rotar SECRET_KEY si se expuso | `config` | ✅ (.gitignore) — pendiente rotación si hubo exposición |
| | 4. `phone_number` → `null=True, blank=True` (+ migración) | `users` | ✅ |
| **P1 — Seguridad e integridad** | 5. Sanitizar errores al cliente (mensaje genérico + log interno) | `queries`, `dataset` | ✅ + `PermissionError`→403 en destroy |
| | 6. Endpoint `token/refresh/` + frontend guarda refresh y llama a logout | `users`, frontend | ✅ backend (`token/refresh/` + `SIMPLE_JWT` con rotación y blacklist) — ⏳ frontend |
| | 7. Exigir `dataset.status == READY` antes de consultar; `DoesNotExist` → 404 | `queries` | ✅ |
| | 8. Normalizar NaN/Timestamp; timeout LLM; límite duro de filas; regex `\blimit\b` | motor IA | ✅ (límite duro vía subquery wrap — la regex ya no hace falta) |
| | 9. Race condition en feedback (`IntegrityError`→400); `transaction.atomic()` en persistencia | `queries` | ✅ |
| | 10. Incluir `{question}` en prompt de corrección; fail-fast en violaciones del validador | motor IA | ✅ (`SecurityError` + `startswith('NO_SQL_POSSIBLE')`) |
| **P2 — Consistencia** | 11. Unificar carga de archivos y heurística de fechas entre SchemaService/Executor | motor IA | ✅ (`SchemaService.read_tables` compartido + `infer_dtype` unificado; sandbox ahora carga las tablas que promete el schema) |
| | 12. Caché: persistir historial en hits, invalidar por versión de dataset, lock anti-stampede | `queries` | ✅ (+ `sha256`, hits cuentan cuota, `query_id` nuevo por hit) |
| | 13. Decidir cuota (activar guard o eliminar `query_count`) | `users`, `queries` | ✅ **Decisión:** conteo consistente sin enforcement (queda para cuando se definan planes; el guard comentado se conserva en `queries/views.py`) |
| | 14. Eliminar código muerto (AuthService.*, repos, ProfileSerializer, blacklist de palabras, MOCK MODE, scope `login`) | varios | ✅ backend (AuthService reducido a `register`, repos muertos, `RegisterSerializer.create`, blacklist, scope `login`, `CreateModelMixin`; `ProfileSerializer` ahora expuesto en `GET/PATCH /users/profile/` + check `is_active` en login) — ⏳ MOCK MODE es frontend (ítem 17) |
| | 15. Serializer ligero para listado de historial (sin `result_json`) | `queries` | ✅ (`QueryHistoryListSerializer`) |
| **P3 — Infra y calidad** | 16. Docker funcional: raíz, Dockerfiles, Postgres/Redis sí o no, gunicorn, healthchecks | infra | ✅ (compose en raíz; Dockerfiles backend/frontend; **decisión:** SQLite + LocMem, que es lo que el código usa — Postgres/Redis/worker eliminados; gunicorn pineado; healthcheck; `pytest`→`requirements-dev.txt`; Ollama sin publicar; `.env.example` completo) |
| | 17. Cablear frontend real (upload + chat + `import.meta.env` + Tailwind en build) | frontend | ✅ (MOCK MODE eliminado; upload/chat/eliminar contra API real; refresh automático + logout con blacklist —cierra ítem 6-; resultados reales con chart/tabla/KPIs; Tailwind en build; toasts en vez de `alert()`; proxy dev en Vite; build verificado 267 KB) |
| | 18. Tests: `users`, `queries`, `services/ai` (hoy 0% en los módulos más críticos) | backend | ✅ 25 tests nuevos en P3 (auth register/login/refresh/logout, perfil, JSON multi-tabla) — suite total: **81 passed** (bug colateral corregido: email duplicado lanzaba `ValidationError` de Django → 500; ahora DRF → 400) |
| | 19. A11y, tree-shaking Chart.js, ESLint/Prettier, `es-co`, squash migraciones | varios | ✅ excepto squash — **decisión: no hacerlo** (riesgo sin beneficio con BD existente; las migraciones ya son consistentes). `es-co` + `America/Bogota`; Chart.js con tree-shaking; drop-zone/chat/botones accesibles; ESLint flat + Prettier configurados y pasando |

---

## 10. Historial

- **24/07/2026 (E2E)** — **Verificación de extremo a extremo con LLM real** (Ollama `qwen2.5-coder:7b`, Django :8000, Vite :5173, API llamada a través del proxy de Vite): register → login → upload CSV (status `ready`, schema correcto) → **pregunta real** (`ventas totales por ciudad` → `SELECT ciudad, SUM(ventas) ... GROUP BY ciudad` → resultados correctos, `chart_type: pie`, 1.2 s, 0 reintentos) → hit de caché con `query_id` nuevo → feedback 201 → historial sin `result_json` → refresh con rotación → logout con blacklist. **Dos bugs encontrados y corregidos:**
  1. `backend/.env` tenía `OLLAMA_HOST` y `KE_LLM_API_KEY` concatenados en una línea → el cliente LLM moría con "missing protocol".
  2. El validador rechazaba el `;` final que el LLM suele añadir (falso positivo de multi-statement) → ahora se normaliza un único `;` terminal antes de validar (+ test de regresión). Suite: **82 passed**.
- **24/07/2026 (P3)** — **Fase P3 (Infra y calidad) resuelta** (ítems 16-19). **Plan de acción completado en su totalidad.**
  - Infra: `docker-compose.yml` movido a la raíz con rutas corregidas; `backend/Dockerfile` (migrate + gunicorn) y `frontend/Dockerfile` (multi-stage Node→nginx con proxy `/api`); servicios Postgres/Redis/worker eliminados (decisión: SQLite + LocMem, que es lo que el código usa); healthcheck en django y `depends_on: service_healthy`; Ollama sin publicar al host; volumen para `MEDIA_ROOT`; `.env.example` completo sin duplicados; `gunicorn` añadido y `pytest*` movido a `requirements-dev.txt`; eliminado `version:` obsoleto.
  - Frontend: MOCK MODE eliminado; `handleUpload`→`api.dataset.upload` (con `name`, `.json` soportado), `sendMessage`→`api.query.ask`, eliminar dataset real; guarda `access`+`refresh`, refresh automático en 401 con rotación, logout llama a blacklist; `API_BASE_URL` por `import.meta.env` con default `/api/v1` (proxy same-origin en dev y compose); Tailwind en el build de Vite (CDN eliminado); KPIs dinámicos (filas/tiempo/fuente), gráfico por `chart_type`+`chart_config` del backend, tabla real (máx. 50 filas); toasts en vez de `alert()`; botón enviar deshabilitado en vuelo; `min_length=5` client-side; a11y (drop-zone con teclado, `aria-live`, `aria-label`); favicon 404 eliminado; Chart.js con tree-shaking; ESLint flat + Prettier configurados (`npm run build` y `lint` verificados: 267 KB JS).
  - Backend: `LANGUAGE_CODE='es-co'`, `TIME_ZONE='America/Bogota'`; `AuthService.register` ahora lanza `ValidationError` de DRF (email duplicado → 400, antes 500).
  - **25 tests nuevos** (auth completo, perfil, JSON multi-tabla). Suite: **81 passed**.
  - Squash de migraciones: **descartado** (riesgo sin beneficio con BD existente).
- **24/07/2026 (P2)** — **Fase P2 (Consistencia) resuelta** (ítems 11-15):
  - Loader único `SchemaService.read_tables` (CSV/JSON multi-tabla/Excel, `ValueError` en extensión no soportada) usado también por `SQLExecutor` → el sandbox SQLite carga exactamente las tablas del schema (cierra bug de JSON multi-tabla del ejecutor). `infer_dtype` unificado → un `date` del schema sigue siendo `date` tras el roundtrip SQLite (los gráficos de línea ya funcionan). Contrato de `extract` aclarado a ruta absoluta.
  - Caché: clave con versión (`updated_at` del dataset, invalidación automática al reprocesar) + `sha256`; los hits persisten `QueryHistory(cached=True)` con `query_id` nuevo (feedback bien anclado, métricas del TFG correctas) y cuentan cuota; lock anti-stampede con `cache.add` + espera acotada.
  - Código muerto eliminado: `AuthService.{login,logout,get_user_by_email,deactivate_user,change_password}`, `RegisterSerializer.create`, `QueryRepository.{get_history,get_by_id}`, blacklist de palabras en `validate_question`, scope `login` huérfano, `CreateModelMixin`. Export de `services/__init__` corregido.
  - `ProfileSerializer` deja de ser código muerto: `GET/PATCH /api/v1/users/profile/` (+ check `is_active` en login).
  - `QueryHistoryListSerializer` sin `result_json` para el listado.
  - **14 tests nuevos** (caché, listado, JSON multi-tabla, perfil). Suite: **71 passed**.
- **24/07/2026** — Ejecución del plan: **P0 (1-4) y P1 backend (5-10) resueltos**. Detalle:
  - Errores al cliente sanitizados con `logger.exception` interno (`queries/views.py`, `dataset/views.py`); `PermissionError`→403 en destroy.
  - `POST /api/v1/users/token/refresh/` publicado + `SIMPLE_JWT` (access 30 min, refresh 7 días, rotación con blacklist).
  - Guard de dataset: `DoesNotExist`→404 (DRF `NotFound`), `status != READY`→400 (`ValidationError`).
  - Motor IA: límite duro de filas con wrap `SELECT * FROM (<sql>) LIMIT 1000` (ineludible); `_json_safe` (NaN→None, Timestamp→ISO, numpy→nativo); timeout LLM 60 s (`OLLAMA_TIMEOUT`); `SecurityError` con fail-fast sin reintentos; `{question}` en prompt de corrección; comparación `startswith('NO_SQL_POSSIBLE')`.
  - Feedback: `IntegrityError`→400 (race condition cerrada); persistencia `save_query`+`save_result` en `transaction.atomic()`.
  - Prints de debug eliminados del flujo de upload.
  - **39 tests nuevos** (queries views/service, validador, prompt builder, executor, orquestador IA). Suite: **57 passed**. Hallazgo colateral: `LocMemCache` contamina entre tests → fixture autouse `cache.clear()` en `conftest.py`.
  - Queda de P1 la parte de **frontend** del ítem 6 (guardar refresh, flujo de refresh, llamar a logout).
- **23/07/2026** — Esta auditoría. Revisión completa backend + frontend + infra, con verificación dinámica (tests ejecutados, introspección de firmas, `manage.py check`). Sustituye íntegramente al documento anterior.
- **01/05/2026** — Auditoría previa (score 3.4/10, solo backend, organizada en 5 fases). Estado de sus recomendaciones:
  - `.gitignore` creado, pero **con `.venv` donde debía decir `.env`** → la recomendación se aplicó mal y la regresión persiste hoy (P0-3).
  - Arquitectura en capas, throttling, blacklist de tokens y validador SQL: aplicados y funcionando.
  - Tests: cobertura parcial solo en `dataset` (16 tests, 1 roto); `users`, `queries` y `services/ai` siguen en 0%.
