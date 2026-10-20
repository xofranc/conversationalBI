export const API_BASE_URL = import.meta.env.VITE_API_URL || "/api/v1";
export const STATUS_ENDPOINT = `${API_BASE_URL}/project-status/`;

export const CHART_COLORS = [
  "#0E5E6F",
  "#3E8FA3",
  "#8FC0C9",
  "#C77B21",
  "#5C6672",
  "#B3402E",
];

export const MAX_TABLE_ROWS = 50;

export const MODULE_STATUS_CONFIG = {
  live: { label: "En producción", color: "bg-petrol", text: "text-petrol" },
  beta: { label: "Beta", color: "bg-signal", text: "text-signal" },
  alpha: {
    label: "Alpha",
    color: "bg-petrol-bright",
    text: "text-petrol-bright",
  },
  pending: { label: "Pendiente", color: "bg-ink-soft", text: "text-ink-soft" },
};

export const PHASE_STATUS_CONFIG = {
  completed: { label: "Completada", color: "bg-petrol", text: "text-petrol" },
  in_progress: {
    label: "En progreso",
    color: "bg-signal",
    text: "text-signal",
  },
  pending: { label: "Pendiente", color: "bg-ink-soft", text: "text-ink-soft" },
  blocked: { label: "Bloqueada", color: "bg-danger", text: "text-danger" },
};

export const STATUS_CONFIG = {
  completed: {
    label: "Completada",
    color: "bg-petrol",
    text: "text-petrol",
    icon: "✓",
  },
  in_progress: {
    label: "En progreso",
    color: "bg-signal",
    text: "text-signal",
    icon: "●",
  },
  pending: {
    label: "Pendiente",
    color: "bg-ink-soft",
    text: "text-ink-soft",
    icon: "○",
  },
  blocked: {
    label: "Bloqueada",
    color: "bg-danger",
    text: "text-danger",
    icon: "!",
  },
};

export const FALLBACK_DATA = {
  project_name: "ConversationalBI",
  tagline: "Hazle preguntas en lenguaje natural a tus datos.",
  phases: [
    {
      id: 1,
      name: "Setup cloud",
      status: "completed",
      description: "Cuentas y variables de entorno configuradas.",
      date_completed: "2026-07-20",
    },
    {
      id: 2,
      name: "Migración LLM",
      status: "completed",
      description: "De Ollama local a OpenCode Go API.",
      date_completed: "2026-07-25",
    },
    {
      id: 3,
      name: "Migración BD",
      status: "completed",
      description: "De SQLite a Supabase Postgres con schema por dataset.",
      date_completed: "2026-07-28",
    },
    {
      id: 4,
      name: "Deploy web",
      status: "completed",
      description: "Render + Vercel + CORS + health check.",
      date_completed: "2026-08-01",
    },
    {
      id: 5,
      name: "Supabase Auth",
      status: "completed",
      description: "Autenticación con JWT RS256 validado en Django.",
      date_completed: "2026-08-05",
    },
    {
      id: 6,
      name: "Copilot analítico",
      status: "in_progress",
      description: "Unificación de conversación, análisis y predicción.",
      date_completed: null,
    },
    {
      id: 7,
      name: "App iOS nativa",
      status: "pending",
      description: "SwiftUI + Swift Charts compartiendo sesión con la web.",
      date_completed: null,
    },
    {
      id: 8,
      name: "Integraciones ERP/POS/CRM",
      status: "pending",
      description: "Conectores nativos para fuentes empresariales.",
      date_completed: null,
    },
  ],
  modules: [
    {
      name: "Conversación sobre datos",
      status: "live",
      description: "Pregunta en español y recibe respuestas conversacionales.",
      icon: "💬",
    },
    {
      name: "Generación de SQL",
      status: "live",
      description: "SQL generado automáticamente por IA y validado.",
      icon: "📜",
    },
    {
      name: "Explicación automática de resultados",
      status: "live",
      description: "Narrativa en lenguaje natural con gráficas.",
      icon: "📝",
    },
    {
      name: "Predicción de ventas",
      status: "live",
      description: "Pronóstico de series temporales con banda de confianza.",
      icon: "📈",
    },
    {
      name: "Predicción de flujo de caja",
      status: "live",
      description: "Proyección de flujos sobre datos históricos.",
      icon: "💰",
    },
    {
      name: "Detección de anomalías",
      status: "live",
      description: "Identificación de valores atípicos con IsolationForest.",
      icon: "🔍",
    },
    {
      name: "Dashboards automáticos",
      status: "beta",
      description: "Colección de visualizaciones guardadas.",
      icon: "📊",
    },
    {
      name: "Memoria de conversaciones",
      status: "live",
      description: "Contexto persistente por dataset.",
      icon: "🧠",
    },
    {
      name: "Detección de fraude",
      status: "pending",
      description: "Reglas y patrones de comportamiento sospechoso.",
      icon: "🛡️",
    },
    {
      name: "Recomendaciones de negocio",
      status: "pending",
      description: "Sugerencias accionables basadas en datos.",
      icon: "💡",
    },
    {
      name: "Integración con ERP/POS/CRM",
      status: "pending",
      description: "Conexión directa con sistemas empresariales.",
      icon: "🔌",
    },
    {
      name: "Agentes especializados",
      status: "pending",
      description: "Agentes de Ventas, Finanzas, Inventario y Contabilidad.",
      icon: "🤖",
    },
  ],
};
