# Auditoría ConversationalBI Backend

> **Fecha:** 01/05/2026 | **Stack:** Django 6.0 + DRF + Ollama + SQLite + Pandas
> **Score:** 3.4 / 10

---

## Índice

- [Fase 1 — Urgente](#fase-1--urgente)
- [Fase 2 — Seguridad](#fase-2--seguridad)
- [Fase 3 — Estabilidad](#fase-3--estabilidad)
- [Fase 4 — Performance](#fase-4--performance)
- [Fase 5 — Production Ready](#fase-5--production-ready)
- [Scorecard](#scorecard)

---

## Fase 1 — Urgente

### 1.1 Crear `.gitignore`

**Problema:** No existe. Archivos sensibles y generados están en el repo.

**Acción:** Crear `.gitignore` en la raíz del backend con:

```gitignore
# Secrets
.env
.env.*
!.env.example

# Database
db.sqlite3
*.sqlite3

# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python
*.so

# Virtual environments
venv/
.venv/
env/
env.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Django
*.log
local_settings.py
staticfiles/

# Media / User data
datasets/
media/

# Testing
.pytest_cache/
.coverage
htmlcov/
.xml

# Build
*.egg-info/
dist/
build/
```

### 1.2 Rotar SECRET_KEY y limpiar historial

**Problema:** La SECRET_KEY está expuesta en `.env` y commiteada en el historial de git.

**Acción:**
1. Generar nueva key: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
2. Actualizar `.env`
3. Crear `.env.example` con valores dummy:
   ```
   SECRET_KEY=change-me-in-production
   DEBUG=False
   OLLAMA_HOST=http://localhost:11434
   OLLAMA_MODEL=qwen2.5-coder:7b
   ```
4. Remover archivos sensibles del historial:
   ```bash
   git rm --cached .env
   git rm --cached db.sqlite3
   git rm --cached .DS_Store
   git rm -r --cached datasets/
   git rm -r --cached **/__pycache__/
   ```

### 1.3 Agregar MEDIA_ROOT y MEDIA_URL a settings

**Archivo:** `config/settings.py`

**Problema:** `FileService` usa `settings.MEDIA_ROOT` pero no está definido.

**Acción:** Agregar después de `STATIC_URL`:

```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### 1.4 Fix LoginView duplicada

**Archivo:** `apps/users/views/auth.py` — línea 36

**Problema:** Clase `LoginView` anidada dentro de sí misma. Código muerto.

**Antes:**
```python
class LoginView(APIView):
    permission_classes = []

    class LoginView(APIView):
        permission_classes = []

    def post(self, request):
        ...
```

**Después:**
```python
class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
```

### 1.5 Fix tests para que corran

#### Test 1: conftest.py — `username` no existe

**Archivo:** `conftest.py` — línea 24

**Problema:** El modelo `User` tiene `username = None`, pero el test usa `username='testuser'`.

**Antes:**
```python
return User.objects.create_user(
    username='testuser',
    email='test@example.com',
    password='testpass123'
)
```

**Después:**
```python
return User.objects.create_user(
    email='test@example.com',
    password='testpass123',
    first_name='Test',
    last_name='User'
)
```

#### Test 2: test_file_service.py — mensaje incorrecto

**Archivo:** `apps/dataset/tests/test_file_service.py` — línea 16

**Problema:** El test espera `match="pesa"` pero el mensaje real dice `"Archivo demasiado grande"`.

**Antes:**
```python
with pytest.raises(ValueError, match="pesa"):
```

**Después:**
```python
with pytest.raises(ValueError, match="demasiado grande"):
```

### 1.6 Agregar configuración de pytest

**Acción:** Crear `pytest.ini` en la raíz:

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = tests.py test_*.py *_tests.py
addopts = -v --tb=short
```

---

## Fase 2 — Seguridad

### 2.1 SQL Validator robusto

**Archivo:** `services/ai/sql_validator.py`

**Problema:** Solo revisa el primer token. Permite multi-statement, UNION, funciones peligrosas de SQLite.

**Ataques que pasan actualmente:**
- `SELECT 1; DROP TABLE users;`
- `SELECT * FROM users UNION SELECT password FROM auth_user`
- `SELECT load_extension('evil.so')`

**Nuevo código:**

```python
import re
import sqlparse
from sqlparse.tokens import DML, Keyword

class SQLValidator:
    ALLOWED = {'SELECT'}

    BLOCKED_PATTERNS = [
        r';',                    # Multi-statement
        r'\bUNION\b',            # UNION injection
        r'\bATTACH\b',           # Attach database
        r'\bDETACH\b',
        r'\bPRAGMA\b',           # SQLite pragma
        r'\bload_extension\b',   # SQLite extensions
        r'\bCREATE\b',
        r'\bINSERT\b',
        r'\bUPDATE\b',
        r'\bDELETE\b',
        r'\bDROP\b',
        r'\bALTER\b',
        r'\bTRUNCATE\b',
        r'\bREPLACE\b',
    ]

    @classmethod
    def assert_safe(cls, sql: str) -> None:
        if not sql or not sql.strip():
            raise ValueError('El SQL está vacío')

        # 1. Bloquear patrones peligrosos
        sql_upper = sql.upper()
        for pattern in cls.BLOCKED_PATTERNS:
            if re.search(pattern, sql_upper):
                raise ValueError(
                    f'Operación no permitida. Solo se aceptan consultas SELECT simples.'
                )

        # 2. Parsear y verificar que sea SELECT
        parsed = sqlparse.parse(sql.strip())
        if not parsed:
            raise ValueError('SQL no parseable')

        statement = parsed[0]
        first_token = statement.token_first(skip_cm=True, skip_ws=True)

        if first_token is None:
            raise ValueError('No se encontró operación válida')

        if first_token.ttype is DML:
            if first_token.normalized.upper() not in cls.ALLOWED:
                raise ValueError(f'Operación no permitida: {first_token.normalized}')
        elif first_token.ttype is Keyword:
            if first_token.normalized.upper() not in cls.ALLOWED:
                raise ValueError(f'Operación no permitida: {first_token.normalized}')
        else:
            raise ValueError('No se encontró una operación SELECT válida')
```

### 2.2 Rate limiting en auth endpoints

**Archivo:** `config/settings.py`

**Problema:** No hay throttle para usuarios anónimos (registro y login).

**Acción:** Agregar en `REST_FRAMEWORK`:

```python
'DEFAULT_THROTTLE_CLASSES': [
    'rest_framework.throttling.UserRateThrottle',
    'rest_framework.throttling.AnonRateThrottle',
],
'DEFAULT_THROTTLE_RATES': {
    'user': '100/hour',
    'anon': '20/hour',      # Registro y login
    'login': '10/hour',     # Específico para login (brute force)
},
```

**Archivo:** `apps/users/views/auth.py`

Agregar throttle a LoginView:

```python
from rest_framework.throttling import AnonRateThrottle

class LoginView(APIView):
    permission_classes = []
    throttle_classes = [AnonRateThrottle]
```

### 2.3 DEBUG desde entorno

**Archivo:** `config/settings.py` — línea 34

**Antes:**
```python
DEBUG = True
```

**Después:**
```python
DEBUG = env('DEBUG', default=False)
```

### 2.4 ALLOWED_HOSTS desde entorno

**Archivo:** `config/settings.py` — línea 36

**Antes:**
```python
ALLOWED_HOSTS = []
```

**Después:**
```python
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])
```

Agregar a `.env.example`:
```
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 2.5 Reemplazar print() con logging

**Archivo:** `apps/users/serializers/auth.py` — línea 75

**Antes:**
```python
print(f"Error al invalidar el token: {str(e)}")
```

**Después:**
```python
import logging

logger = logging.getLogger(__name__)

# ...
logger.warning(f"Error al invalidar el token: {str(e)}")
```

### 2.6 Remover datos de usuario del repo

**Problema:** `datasets/5/ac0cdf2747b94a30951193399cef121d.csv` contiene datos reales.

**Acción:**
```bash
git rm --cached datasets/5/ac0cdf2747b94a30951193399cef121d.csv
git rm -r --cached datasets/
```

---

## Fase 3 — Estabilidad

### 3.1 Agregar dependencias faltantes con versiones

**Archivo:** `requirements.txt`

**Antes:**
```
Django
Pandas
numpy
pytest-django
sqlparse
djangorestframework
djangorestframework-simplejwt
```

**Después:**
```
Django>=5.0,<6.1
djangorestframework>=3.15,<4.0
djangorestframework-simplejwt>=5.3,<6.0
django-environ>=0.11,<1.0
pandas>=2.2,<3.0
numpy>=1.26,<3.0
pytest-django>=4.8,<5.0
sqlparse>=0.5,<1.0
langchain-ollama>=0.1,<1.0
openpyxl>=3.1,<4.0
python-dateutil>=2.9,<3.0
```

### 3.2 Fix duplicación de registro (serializer vs service)

**Problema:** `RegisterView` usa `RegisterSerializer.create()` que crea el User pero NO el Profile. `AuthService.register()` sí lo crea pero no se usa.

**Opción A — Usar el Service en la View:**

**Archivo:** `apps/users/views/auth.py`

```python
class RegisterView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = AuthService.register(
            email      = serializer.validated_data['email'],
            password   = serializer.validated_data['password'],
            first_name = serializer.validated_data['first_name'],
            last_name  = serializer.validated_data['last_name'],
        )

        return Response({
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }, status=status.HTTP_201_CREATED)
```

**Opción B — Signal para crear Profile automáticamente:**

Crear `apps/users/signals.py`:

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Profile

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
```

Agregar en `apps/users/apps.py`:

```python
from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'

    def ready(self):
        import apps.users.signals  # noqa
```

### 3.3 Fix paginación en QueryHistory list

**Archivo:** `apps/queries/views.py` — línea 65-71

**Problema:** El `list()` manual ignora la paginación configurada en DRF.

**Antes:**
```python
def list(self, request):
    dataset_id = request.query_params.get('dataset_id')
    qs         = self.get_queryset()
    if dataset_id:
        qs = qs.filter(dataset_id=dataset_id)
    serializer = QueryHistorySerializer(qs, many=True)
    return Response(serializer.data)
```

**Después:**
```python
def list(self, request):
    dataset_id = request.query_params.get('dataset_id')
    qs = self.get_queryset()
    if dataset_id:
        qs = qs.filter(dataset_id=dataset_id)

    page = self.paginate_queryset(qs)
    if page is not None:
        serializer = QueryHistorySerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    serializer = QueryHistorySerializer(qs, many=True)
    return Response(serializer.data)
```

### 3.4 Implementar soporte .json o removerlo

**Decisión:** O implementar o remover de las extensiones permitidas.

**Si se remueve:**

**Archivo:** `apps/dataset/services/file_service.py` — línea 6
```python
ALLOWED_EXTENSIONS = ['.csv', '.xlsx']
```

**Archivo:** `apps/dataset/serializers/datasetUpload.py` — línea 12
```python
allowed_extensions = ['.csv', '.xlsx']
```

**Si se implementa:** Agregar en `SchemaService._read_file()`:

```python
@staticmethod
def _read_file(abs_path: str, ext: str) -> dict:
    if ext == ".csv":
        return {"main": pd.read_csv(abs_path)}
    if ext == ".json":
        df = pd.read_json(abs_path)
        if isinstance(df, dict):
            return {k: pd.DataFrame(v) for k, v in df.items()}
        return {"main": df}
    xls = pd.ExcelFile(abs_path)
    return {name: xls.parse(name) for name in xls.sheet_names}
```

Y en `SQLExecutor._load_into_sqlite()`:

```python
if ext == '.csv':
    df = pd.read_csv(file_path)
    table_name = schema_json.get('tables', [{}])[0].get('name', 'main')
    df.to_sql(table_name, conn, index=False, if_exists='replace')
elif ext == '.json':
    df = pd.read_json(file_path)
    if isinstance(df, dict):
        for k, v in df.items():
            pd.DataFrame(v).to_sql(k, conn, index=False, if_exists='replace')
    else:
        df.to_sql('main', conn, index=False, if_exists='replace')
else:
    xls = pd.ExcelFile(file_path)
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        df.to_sql(sheet, conn, index=False, if_exists='replace')
```

### 3.5 Eliminar user_type_id redundante

**Archivo:** `apps/users/models.py` — línea 67

**Problema:** Mantener dos campos sincronizados es antipatrón.

**Acción:** Eliminar `user_type_id`, `USER_TYPE_ID_MAP`, y el override de `save()` que los sincroniza. Si se necesita un ID numérico para queries, usar directamente `user_type` con una propiedad:

```python
@property
def user_type_numeric(self):
    return {'USER': 1, 'ADMIN': 2}.get(self.user_type, 0)
```

### 3.6 Mover validación de phone_number al serializer

**Archivo:** `apps/users/serializers/profile.py`

**Acción:** Agregar validator:

```python
class ProfileSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(max_length=10, required=False, allow_blank=True)

    class Meta:
        model = Profile
        fields = ['bio', 'phone_number', 'birth_date']

    def validate_phone_number(self, value):
        if value and not value.isdigit():
            raise serializers.ValidationError('El teléfono debe contener solo dígitos')
        if value and len(value) != 10:
            raise serializers.ValidationError('El teléfono debe tener 10 dígitos')
        return value
```

Y simplificar el `Profile.save()`:

```python
def save(self, *args, **kwargs):
    super().save(*args, **kwargs)
```

### 3.7 Eliminar archivos vacíos y limpios

| Archivo | Acción |
|---------|--------|
| `apps/users/views/profile.py` | Implementar o eliminar |
| `apps/queries/tests.py` | Eliminar (se usa pytest) |
| `apps/users/tests.py` | Eliminar (se usa pytest) |
| `apps/queries/admin.py` | Registrar modelos o eliminar imports |
| `apps/users/admin.py` | Registrar modelos |

**Admin sugerido para queries:**

```python
from django.contrib import admin
from .models import QueryHistory, QueryResult, QueryFeedback

@admin.register(QueryHistory)
class QueryHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'success', 'model_used', 'created_at')
    list_filter = ('success', 'model_used', 'cached')
    search_fields = ('question', 'sql_generated')

@admin.register(QueryResult)
class QueryResultAdmin(admin.ModelAdmin):
    list_display = ('query_id', 'row_count', 'chart_type')

@admin.register(QueryFeedback)
class QueryFeedbackAdmin(admin.ModelAdmin):
    list_display = ('query_id', 'score', 'created_at')
    list_filter = ('score',)
```

---

## Fase 4 — Performance

### 4.1 SQLite persistente entre queries

**Problema:** Cada query lee el archivo completo del disco y lo carga en SQLite en memoria.

**Archivo:** `services/ai/sql_executor.py`

**Solución:** Crear un cache de conexiones SQLite por dataset.

```python
import threading

_sqlite_cache = {}
_cache_lock = threading.Lock()

class SQLExecutor:
    @staticmethod
    def run(sql: str, dataset_id: int) -> tuple[list, list]:
        from apps.dataset.repositories import DatasetRepository
        dataset = DatasetRepository.get_by_id(dataset_id)

        conn = SQLExecutor._get_connection(dataset)

        try:
            df = pd.read_sql_query(sql, conn)
        except Exception as e:
            raise ValueError(f"Error ejecutando SQL: {e}")

        columns = [
            {'name': col, 'dtype': SQLExecutor._dtype(df[col])}
            for col in df.columns
        ]
        rows = df.to_dict(orient='records')

        return rows, columns

    @staticmethod
    def _get_connection(dataset) -> sqlite3.Connection:
        file_path = os.path.join(settings.MEDIA_ROOT, dataset.file_path)
        cache_key = f"{dataset.id}:{dataset.updated_at}"

        with _cache_lock:
            if cache_key in _sqlite_cache:
                return _sqlite_cache[cache_key]

            conn = SQLExecutor._load_into_sqlite(file_path, dataset)
            _sqlite_cache[cache_key] = conn
            return conn
```

**Alternativa mejor:** Evaluar **DuckDB** como motor de ejecución SQL. Es 10-100x más rápido que SQLite para consultas analíticas sobre CSV/Parquet.

### 4.2 LIMIT forzado en queries del LLM

**Problema:** El LLM puede generar `SELECT * FROM tabla` sin límite.

**Archivo:** `services/ai/sql_executor.py`

**Solución:** Agregar límite por defecto si no hay LIMIT:

```python
MAX_ROWS = 1000

@staticmethod
def run(sql: str, dataset_id: int) -> tuple[list, list]:
    # Agregar LIMIT si no existe
    sql_lower = sql.strip().lower()
    if 'limit' not in sql_lower:
        sql = f"{sql.rstrip(';')} LIMIT {MAX_ROWS}"

    # ... resto del código
```

### 4.3 Migrar a Redis para cache

**Archivo:** `config/settings.py`

**Antes:**
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
```

**Después:**
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://localhost:6379/0'),
    }
}
```

Agregar a `requirements.txt`:
```
redis>=5.0,<6.0
```

Agregar a `.env.example`:
```
REDIS_URL=redis://localhost:6379/0
```

---

## Fase 5 — Production Ready

### 5.1 Logging estructurado

**Archivo:** `config/settings.py`

Agregar al final:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'app.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'services.ai': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

Crear directorio: `mkdir -p backend/logs && touch backend/logs/.gitkeep`

### 5.2 ALLOWED_HOSTS y CORS

Agregar a `requirements.txt`:
```
django-cors-headers>=4.3,<5.0
```

**Archivo:** `config/settings.py`

```python
INSTALLED_APPS = [
    # ...
    'corsheaders',
    # ...
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # ← antes de CommonMiddleware
    'django.middleware.security.SecurityMiddleware',
    # ... resto
]

CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://localhost:3000',
    'http://localhost:5173',
])

CORS_ALLOW_CREDENTIALS = True
```

### 5.3 Health check endpoint

**Acción:** Crear `apps/core/` app o agregar en urls raíz.

```python
# config/urls.py
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({'status': 'ok', 'timestamp': timezone.now().isoformat()})

urlpatterns = [
    path('health/', health_check, name='health'),
    # ...
]
```

### 5.4 Security middleware para producción

**Archivo:** `config/settings.py`

Agregar después de `ALLOWED_HOSTS`:

```python
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
```

### 5.5 JWT Settings

**Archivo:** `config/settings.py`

Agregar:

```python
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

---

## Scorecard

| Categoría | Score | Peso | Ponderado |
|-----------|:-----:|:----:|:---------:|
| Seguridad | 2/10 | 25% | 0.5 |
| Arquitectura | 6/10 | 20% | 1.2 |
| Testing | 2/10 | 20% | 0.4 |
| Performance | 4/10 | 15% | 0.6 |
| Code Quality | 5/10 | 10% | 0.5 |
| Deployment Ready | 2/10 | 10% | 0.2 |
| **TOTAL** | | **100%** | **3.4 / 10** |

---

## Checklist de progreso

### Fase 1 — Urgente
- [ ] 1.1 Crear `.gitignore`
- [ ] 1.2 Rotar SECRET_KEY + `.env.example`
- [ ] 1.3 Agregar MEDIA_ROOT y MEDIA_URL
- [ ] 1.4 Fix LoginView duplicada
- [ ] 1.5 Fix tests (conftest + test_file_service)
- [ ] 1.6 Crear `pytest.ini`

### Fase 2 — Seguridad
- [ ] 2.1 SQL Validator robusto
- [ ] 2.2 Rate limiting en auth
- [ ] 2.3 DEBUG desde entorno
- [ ] 2.4 ALLOWED_HOSTS desde entorno
- [ ] 2.5 Reemplazar print() con logging
- [ ] 2.6 Remover datos de usuario del repo

### Fase 3 — Estabilidad
- [ ] 3.1 Dependencias con versiones
- [ ] 3.2 Fix duplicación de registro
- [ ] 3.3 Fix paginación QueryHistory
- [ ] 3.4 Implementar/remover soporte .json
- [ ] 3.5 Eliminar user_type_id redundante
- [ ] 3.6 Mover validación phone al serializer
- [ ] 3.7 Eliminar archivos vacíos

### Fase 4 — Performance
- [ ] 4.1 SQLite persistente entre queries
- [ ] 4.2 LIMIT forzado en queries
- [ ] 4.3 Migrar a Redis cache

### Fase 5 — Production Ready
- [ ] 5.1 Logging estructurado
- [ ] 5.2 CORS configurado
- [ ] 5.3 Health check endpoint
- [ ] 5.4 Security middleware para producción
- [ ] 5.5 JWT settings configurados
