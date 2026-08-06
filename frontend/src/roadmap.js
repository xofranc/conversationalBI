import './styles.css';
import './landing.css';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

const REDUCED = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const API_URL = import.meta.env.VITE_API_URL || '/api/v1';
const STATUS_ENDPOINT = `${API_URL}/project-status/`;

const STATUS_CONFIG = {
  completed: { label: 'Completada', color: 'bg-petrol', text: 'text-petrol', icon: '✓' },
  in_progress: { label: 'En progreso', color: 'bg-signal', text: 'text-signal', icon: '●' },
  pending: { label: 'Pendiente', color: 'bg-ink-soft', text: 'text-ink-soft', icon: '○' },
  blocked: { label: 'Bloqueada', color: 'bg-danger', text: 'text-danger', icon: '!' },
};

const MODULE_STATUS_CONFIG = {
  live: { label: 'En producción', color: 'bg-petrol', text: 'text-petrol' },
  beta: { label: 'Beta', color: 'bg-signal', text: 'text-signal' },
  alpha: { label: 'Alpha', color: 'bg-petrol-bright', text: 'text-petrol-bright' },
  pending: { label: 'Pendiente', color: 'bg-ink-soft', text: 'text-ink-soft' },
};

const FALLBACK_DATA = {
  project_name: 'ConversationalBI',
  tagline: 'Hazle preguntas en lenguaje natural a tus datos.',
  phases: [
    { id: 1, name: 'Setup cloud', status: 'completed', description: 'Cuentas y variables de entorno configuradas.', date_completed: '2026-07-20' },
    { id: 2, name: 'Migración LLM', status: 'completed', description: 'De Ollama local a OpenCode Go API.', date_completed: '2026-07-25' },
    { id: 3, name: 'Migración BD', status: 'completed', description: 'De SQLite a Supabase Postgres con schema por dataset.', date_completed: '2026-07-28' },
    { id: 4, name: 'Deploy web', status: 'completed', description: 'Render + Vercel + CORS + health check.', date_completed: '2026-08-01' },
    { id: 5, name: 'Supabase Auth', status: 'completed', description: 'Autenticación con JWT RS256 validado en Django.', date_completed: '2026-08-05' },
    { id: 6, name: 'Copilot analítico', status: 'in_progress', description: 'Unificación de conversación, análisis y predicción.', date_completed: null },
    { id: 7, name: 'App iOS nativa', status: 'pending', description: 'SwiftUI + Swift Charts compartiendo sesión con la web.', date_completed: null },
    { id: 8, name: 'Integraciones ERP/POS/CRM', status: 'pending', description: 'Conectores nativos para fuentes empresariales.', date_completed: null },
  ],
  modules: [
    { name: 'Conversación sobre datos', status: 'live', description: 'Pregunta en español y recibe respuestas conversacionales.', icon: '💬' },
    { name: 'Generación de SQL', status: 'live', description: 'SQL generado automáticamente por IA y validado.', icon: '📜' },
    { name: 'Explicación automática de resultados', status: 'live', description: 'Narrativa en lenguaje natural con gráficas.', icon: '📝' },
    { name: 'Predicción de ventas', status: 'live', description: 'Pronóstico de series temporales con banda de confianza.', icon: '📈' },
    { name: 'Predicción de flujo de caja', status: 'live', description: 'Proyección de flujos sobre datos históricos.', icon: '💰' },
    { name: 'Detección de anomalías', status: 'live', description: 'Identificación de valores atípicos con IsolationForest.', icon: '🔍' },
    { name: 'Detección de fraude', status: 'pending', description: 'Reglas y patrones de comportamiento sospechoso.', icon: '🛡️' },
    { name: 'Recomendaciones de negocio', status: 'pending', description: 'Sugerencias accionables basadas en datos.', icon: '💡' },
    { name: 'Integración con ERP/POS/CRM', status: 'pending', description: 'Conexión directa con sistemas empresariales.', icon: '🔌' },
    { name: 'Dashboards generados automáticamente', status: 'beta', description: 'Colección de visualizaciones guardadas.', icon: '📊' },
    { name: 'Memoria de conversaciones', status: 'live', description: 'Contexto persistente por dataset.', icon: '🧠' },
    { name: 'Agentes especializados', status: 'pending', description: 'Agentes de Ventas, Finanzas, Inventario y Contabilidad.', icon: '🤖' },
  ],
};

function formatDate(dateStr) {
  if (!dateStr) return null;
  const d = new Date(dateStr);
  return d.toLocaleDateString('es-CO', { month: 'short', year: 'numeric' });
}

function renderTimeline(phases) {
  const container = document.getElementById('timeline');
  const line = container.querySelector('.absolute');

  phases.forEach((phase, index) => {
    const cfg = STATUS_CONFIG[phase.status] || STATUS_CONFIG.pending;
    const isLeft = index % 2 === 0;
    const dateLabel = formatDate(phase.date_completed);

    const item = document.createElement('div');
    item.className = `timeline-item relative flex items-center justify-between lg:justify-normal gap-8 mb-12 ${isLeft ? 'lg:flex-row-reverse' : ''}`;
    item.innerHTML = `
      <div class="hidden lg:block w-5/12"></div>
      <div class="timeline-node z-10 w-10 h-10 rounded-full ${cfg.color} flex items-center justify-center text-white text-sm font-bold shadow-lift shrink-0">
        ${cfg.icon}
      </div>
      <div class="timeline-card w-full lg:w-5/12 bg-card border border-line rounded-xl p-6 shadow-card">
        <div class="flex items-center gap-3 mb-3">
          <span class="font-mono text-[0.6rem] tracking-[0.2em] uppercase ${cfg.text}">${cfg.label}</span>
          ${dateLabel ? `<span class="ml-auto font-mono text-[0.6rem] text-ink-soft">${dateLabel}</span>` : ''}
        </div>
        <h3 class="font-display text-xl font-semibold text-ink mb-2">${phase.name}</h3>
        <p class="text-sm text-ink-soft leading-relaxed">${phase.description}</p>
      </div>
    `;
    container.appendChild(item);
  });
}

function renderModules(modules) {
  const grid = document.getElementById('modules-grid');

  modules.forEach((mod) => {
    const cfg = MODULE_STATUS_CONFIG[mod.status] || MODULE_STATUS_CONFIG.pending;
    const card = document.createElement('div');
    card.className = 'module-card bg-paper border border-line rounded-xl p-6 transition-all duration-300 hover:-translate-y-2 hover:shadow-lift hover:border-petrol';
    card.innerHTML = `
      <div class="flex items-start justify-between mb-4">
        <span class="text-2xl">${mod.icon || '◆'}</span>
        <span class="font-mono text-[0.58rem] tracking-wider uppercase px-2 py-1 rounded ${cfg.color}/10 ${cfg.text}">${cfg.label}</span>
      </div>
      <h3 class="font-display text-lg font-semibold text-ink mb-2">${mod.name}</h3>
      <p class="text-sm text-ink-soft leading-relaxed">${mod.description}</p>
    `;
    grid.appendChild(card);
  });
}

function updateProgress(phases) {
  const completed = phases.filter((p) => p.status === 'completed').length;
  const inProgress = phases.filter((p) => p.status === 'in_progress').length;
  const total = phases.length;
  const progress = Math.round(((completed + inProgress * 0.5) / total) * 100);

  document.getElementById('progress-bar').style.width = `${progress}%`;
  document.getElementById('progress-text').textContent = `${progress}%`;
}

function animate() {
  if (REDUCED) return;

  gsap.from('#progress-bar', {
    width: '0%',
    duration: 1.2,
    ease: 'power2.out',
  });

  gsap.utils.toArray('.timeline-item').forEach((item, i) => {
    gsap.from(item, {
      y: 40,
      opacity: 0,
      duration: 0.7,
      ease: 'power3.out',
      scrollTrigger: {
        trigger: item,
        start: 'top 85%',
        once: true,
      },
      delay: i * 0.08,
    });
  });

  gsap.utils.toArray('.module-card').forEach((card, i) => {
    gsap.from(card, {
      y: 24,
      opacity: 0,
      duration: 0.6,
      ease: 'power3.out',
      scrollTrigger: {
        trigger: card,
        start: 'top 88%',
        once: true,
      },
      delay: i * 0.05,
    });
  });
}

async function loadData() {
  try {
    const response = await fetch(STATUS_ENDPOINT);
    if (!response.ok) throw new Error('Network response was not ok');
    const data = await response.json();
    return data;
  } catch (err) {
    console.warn('No se pudo cargar el estado del proyecto; usando datos locales.', err);
    return FALLBACK_DATA;
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  const data = await loadData();
  renderTimeline(data.phases || FALLBACK_DATA.phases);
  renderModules(data.modules || FALLBACK_DATA.modules);
  updateProgress(data.phases || FALLBACK_DATA.phases);
  animate();
});
