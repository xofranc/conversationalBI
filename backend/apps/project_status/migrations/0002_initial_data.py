# Initial data for project phases and modules

from django.db import migrations


PHASES = [
    {"order": 1, "name": "Setup cloud", "status": "completed", "description": "Cuentas y variables de entorno configuradas.", "date_completed": "2026-07-20"},
    {"order": 2, "name": "Migración LLM", "status": "completed", "description": "De Ollama local a OpenCode Go API.", "date_completed": "2026-07-25"},
    {"order": 3, "name": "Migración BD", "status": "completed", "description": "De SQLite a Supabase Postgres con schema por dataset.", "date_completed": "2026-07-28"},
    {"order": 4, "name": "Deploy web", "status": "completed", "description": "Render + Vercel + CORS + health check.", "date_completed": "2026-08-01"},
    {"order": 5, "name": "Supabase Auth", "status": "completed", "description": "Autenticación con JWT RS256 validada en Django.", "date_completed": "2026-08-05"},
    {"order": 6, "name": "Copilot analítico", "status": "in_progress", "description": "Unificación de conversación, análisis y predicción.", "date_completed": None},
    {"order": 7, "name": "App iOS nativa", "status": "pending", "description": "SwiftUI + Swift Charts compartiendo sesión con la web.", "date_completed": None},
    {"order": 8, "name": "Integraciones ERP/POS/CRM", "status": "pending", "description": "Conectores nativos para fuentes empresariales.", "date_completed": None},
]

MODULES = [
    {"order": 1, "name": "Conversación sobre datos", "status": "live", "description": "Pregunta en español y recibe respuestas conversacionales.", "icon": "💬"},
    {"order": 2, "name": "Generación de SQL", "status": "live", "description": "SQL generado automáticamente por IA y validado.", "icon": "📜"},
    {"order": 3, "name": "Explicación automática de resultados", "status": "live", "description": "Narrativa en lenguaje natural con gráficas.", "icon": "📝"},
    {"order": 4, "name": "Predicción de ventas", "status": "live", "description": "Pronóstico de series temporales con banda de confianza.", "icon": "📈"},
    {"order": 5, "name": "Predicción de flujo de caja", "status": "live", "description": "Proyección de flujos sobre datos históricos.", "icon": "💰"},
    {"order": 6, "name": "Detección de anomalías", "status": "live", "description": "Identificación de valores atípicos con IsolationForest.", "icon": "🔍"},
    {"order": 7, "name": "Detección de fraude", "status": "pending", "description": "Reglas y patrones de comportamiento sospechoso.", "icon": "🛡️"},
    {"order": 8, "name": "Recomendaciones de negocio", "status": "pending", "description": "Sugerencias accionables basadas en datos.", "icon": "💡"},
    {"order": 9, "name": "Integración con ERP/POS/CRM", "status": "pending", "description": "Conexión directa con sistemas empresariales.", "icon": "🔌"},
    {"order": 10, "name": "Dashboards generados automáticamente", "status": "beta", "description": "Colección de visualizaciones guardadas.", "icon": "📊"},
    {"order": 11, "name": "Memoria de conversaciones", "status": "live", "description": "Contexto persistente por dataset.", "icon": "🧠"},
    {"order": 12, "name": "Agentes especializados", "status": "pending", "description": "Agentes de Ventas, Finanzas, Inventario y Contabilidad.", "icon": "🤖"},
]


def seed_data(apps, schema_editor):
    ProjectPhase = apps.get_model('project_status', 'ProjectPhase')
    ProjectModule = apps.get_model('project_status', 'ProjectModule')

    for data in PHASES:
        ProjectPhase.objects.get_or_create(order=data['order'], defaults=data)

    for data in MODULES:
        ProjectModule.objects.get_or_create(order=data['order'], defaults=data)


def clear_data(apps, schema_editor):
    ProjectPhase = apps.get_model('project_status', 'ProjectPhase')
    ProjectModule = apps.get_model('project_status', 'ProjectModule')
    ProjectPhase.objects.all().delete()
    ProjectModule.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('project_status', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_data, reverse_code=clear_data),
    ]
