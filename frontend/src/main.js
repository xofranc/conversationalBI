import './styles.css';
import { api } from './api.js';
import { animations } from './animations.js';
import {
  Chart,
  BarController, BarElement,
  LineController, LineElement,
  PieController, ArcElement,
  ScatterController, PointElement,
  CategoryScale, LinearScale,
  Tooltip, Legend, Filler,
} from 'chart.js';

Chart.register(
  BarController, BarElement,
  LineController, LineElement,
  PieController, ArcElement,
  ScatterController, PointElement,
  CategoryScale, LinearScale,
  Tooltip, Legend, Filler,
);

// App State
let currentDatasetId = null;
let resultChart = null;
let sending = false;
let toastTimer = null;

const CHART_COLORS = ['#14b8a6', '#8b5cf6', '#f43f5e', '#f59e0b', '#3b82f6', '#10b981'];
const MAX_TABLE_ROWS = 50;

document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('login-form');
  const registerForm = document.getElementById('register-form');
  const authSubtitle = document.getElementById('auth-subtitle');
  const errorEl = document.getElementById('auth-error');
  const chatInput = document.getElementById('chat-input');
  const sendBtn = document.getElementById('send-btn');
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-upload');

  // Sesión activa → directo al dashboard
  if (api.getToken()) {
    enterDashboard(false);
  }

  // ── Auth: toggle login/registro ─────────────────────────────────────────
  document.getElementById('show-register').addEventListener('click', (e) => {
    e.preventDefault();
    errorEl.classList.add('hidden');
    loginForm.classList.add('hidden');
    registerForm.classList.remove('hidden');
    authSubtitle.innerText = 'Crea una cuenta para continuar';
  });

  document.getElementById('show-login').addEventListener('click', (e) => {
    e.preventDefault();
    errorEl.classList.add('hidden');
    registerForm.classList.add('hidden');
    loginForm.classList.remove('hidden');
    authSubtitle.innerText = 'Inicia sesión para continuar';
  });

  // ── Login ───────────────────────────────────────────────────────────────
  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    try {
      errorEl.classList.add('hidden');
      animations.showLoader('Iniciando sesión...');
      const res = await api.auth.login(email, password);

      if (!res.access || !res.refresh) throw new Error('Tokens no recibidos');
      api.setTokens(res.access, res.refresh);
      animations.hideLoader();
      enterDashboard(true);
    } catch (err) {
      animations.hideLoader();
      errorEl.innerText = err.data?.detail || err.data?.non_field_errors?.[0] || 'Error al iniciar sesión. Verifica tus credenciales.';
      errorEl.classList.remove('hidden');
    }
  });

  // ── Registro ────────────────────────────────────────────────────────────
  registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const firstName = document.getElementById('reg-first-name').value;
    const lastName = document.getElementById('reg-last-name').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;

    try {
      errorEl.classList.add('hidden');
      animations.showLoader('Creando cuenta...');
      await api.auth.register(email, password, firstName, lastName);
      const res = await api.auth.login(email, password);

      if (!res.access || !res.refresh) throw new Error('Tokens no recibidos');
      api.setTokens(res.access, res.refresh);
      animations.hideLoader();
      enterDashboard(true);
    } catch (err) {
      animations.hideLoader();
      errorEl.innerText = parseDrfError(err) || 'Error al crear la cuenta.';
      errorEl.classList.remove('hidden');
    }
  });

  // ── Logout ──────────────────────────────────────────────────────────────
  document.getElementById('logout-btn').addEventListener('click', async () => {
    try {
      await api.auth.logout();   // blacklist del refresh token en el backend
    } catch {
      // Si falla (red, token ya inválido), igual limpiamos la sesión local
    }
    forceLogout();
  });

  function forceLogout() {
    api.clearTokens();
    currentDatasetId = null;
    hideActiveDataset();
    animations.logout();
  }

  function enterDashboard(animate) {
    if (animate) {
      animations.loginSuccess();
    } else {
      document.getElementById('auth-view').classList.add('hidden');
      const dashboard = document.getElementById('dashboard-view');
      dashboard.classList.remove('hidden');
      dashboard.style.opacity = '1';
    }
  }

  // ── Upload ──────────────────────────────────────────────────────────────
  dropZone.addEventListener('click', () => fileInput.click());
  dropZone.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      fileInput.click();
    }
  });

  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('border-teal', 'bg-teal/5');
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('border-teal', 'bg-teal/5');
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('border-teal', 'bg-teal/5');
    if (e.dataTransfer.files.length) handleUpload(e.dataTransfer.files[0]);
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) handleUpload(e.target.files[0]);
  });

  async function handleUpload(file) {
    const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
    if (!['.csv', '.xlsx', '.json'].includes(ext)) {
      showToast('Solo se permiten archivos CSV, Excel o JSON.', 'error');
      return;
    }

    try {
      animations.showLoader('Procesando dataset...');
      const name = file.name.replace(/\.[^.]+$/, '');
      const dataset = await api.dataset.upload(file, name);

      currentDatasetId = dataset.id;
      showActiveDataset(dataset.name);
      addMessageToChat(
        'AI',
        `¡Dataset "${dataset.name}" listo! ${dataset.row_count} filas y ${dataset.column_count} columnas. ¿Qué quieres saber?`
      );
    } catch (err) {
      handleApiError(err, 'Error al cargar el archivo.');
    } finally {
      animations.hideLoader();
      fileInput.value = '';
    }
  }

  function showActiveDataset(name) {
    dropZone.classList.add('hidden');
    document.getElementById('dataset-name').innerText = name;
    document.getElementById('active-dataset').classList.remove('hidden');
  }

  function hideActiveDataset() {
    dropZone.classList.remove('hidden');
    document.getElementById('active-dataset').classList.add('hidden');
    fileInput.value = '';
    currentDatasetId = null;
  }

  document.getElementById('remove-dataset').addEventListener('click', async () => {
    if (currentDatasetId) {
      try {
        await api.dataset.delete(currentDatasetId);
      } catch {
        // Si ya no existe en el backend, igual se desvincula localmente
      }
    }
    hideActiveDataset();
    showToast('Dataset eliminado.', 'success');
  });

  // ── Chat ────────────────────────────────────────────────────────────────
  const sendMessage = async () => {
    const text = chatInput.value.trim();
    if (text.length < 5) {
      showToast('La pregunta debe tener al menos 5 caracteres.', 'error');
      return;
    }
    if (!currentDatasetId) {
      showToast('Por favor, sube un dataset primero.', 'error');
      return;
    }
    if (sending) return;

    sending = true;
    sendBtn.disabled = true;
    addMessageToChat('User', text);
    chatInput.value = '';

    try {
      const res = await api.query.ask(text, currentDatasetId);

      if (res.success) {
        addMessageToChat(
          'AI',
          `Encontré ${res.row_count} fila(s) en ${res.execution_time}s${res.cached ? ' (desde caché)' : ''}.`
        );
        renderResult(res);
      } else {
        addMessageToChat('AI', `No pude responder esa pregunta: ${res.error_msg || 'error desconocido'}.`);
      }
    } catch (err) {
      handleApiError(err, 'Ocurrió un error al procesar la consulta.');
    } finally {
      sending = false;
      sendBtn.disabled = false;
      chatInput.focus();
    }
  };

  sendBtn.addEventListener('click', sendMessage);
  chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
  });

  // ── Render de resultados reales ─────────────────────────────────────────
  function renderResult(res) {
    animations.revealChart();

    document.getElementById('kpi-rows').innerText = res.row_count;
    document.getElementById('kpi-time').innerText = `${res.execution_time}s`;
    document.getElementById('kpi-source').innerText = res.cached ? 'Caché' : (res.model_used || 'IA');

    renderChart(res);
    renderTable(res);
  }

  function renderChart(res) {
    const container = document.getElementById('chart-container');

    if (resultChart) {
      resultChart.destroy();
      resultChart = null;
    }

    if (res.chart_type === 'table' || !res.data?.length) {
      container.classList.add('hidden');
      return;
    }

    container.classList.remove('hidden');
    const cfg = res.chart_config || {};
    const ctx = document.getElementById('chart-1').getContext('2d');

    const baseOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#e2e8f0' } } },
    };

    if (res.chart_type === 'pie') {
      resultChart = new Chart(ctx, {
        type: 'pie',
        data: {
          labels: res.data.map((r) => r[cfg.nameKey]),
          datasets: [{
            data: res.data.map((r) => r[cfg.valueKey]),
            backgroundColor: CHART_COLORS,
            borderWidth: 0,
          }],
        },
        options: baseOptions,
      });
      return;
    }

    if (res.chart_type === 'scatter') {
      resultChart = new Chart(ctx, {
        type: 'scatter',
        data: {
          datasets: [{
            label: `${cfg.xKey} vs ${cfg.yKey}`,
            data: res.data.map((r) => ({ x: r[cfg.xKey], y: r[cfg.yKey] })),
            backgroundColor: '#14b8a6',
          }],
        },
        options: {
          ...baseOptions,
          scales: {
            y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
            x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
          },
        },
      });
      return;
    }

    // bar / line
    resultChart = new Chart(ctx, {
      type: res.chart_type,
      data: {
        labels: res.data.map((r) => r[cfg.xKey]),
        datasets: [{
          label: cfg.yKey,
          data: res.data.map((r) => r[cfg.yKey]),
          backgroundColor: res.chart_type === 'bar' ? 'rgba(20, 184, 166, 0.7)' : 'rgba(20, 184, 166, 0.2)',
          borderColor: '#14b8a6',
          fill: res.chart_type === 'line',
          tension: 0.4,
        }],
      },
      options: {
        ...baseOptions,
        scales: {
          y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
          x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
        },
      },
    });
  }

  function renderTable(res) {
    const tHead = document.getElementById('table-head');
    const tBody = document.getElementById('table-body');
    tHead.innerHTML = '';
    tBody.innerHTML = '';

    const cols = (res.columns?.length ? res.columns.map((c) => c.name) : Object.keys(res.data?.[0] || {}));
    cols.forEach((col) => {
      const th = document.createElement('th');
      th.className = 'px-6 py-3';
      th.innerText = col;
      tHead.appendChild(th);
    });

    res.data.slice(0, MAX_TABLE_ROWS).forEach((row) => {
      const tr = document.createElement('tr');
      cols.forEach((col) => {
        const td = document.createElement('td');
        td.className = 'px-6 py-4 whitespace-nowrap';
        const val = row[col];
        td.innerText = val === null || val === undefined ? '—' : val;
        tr.appendChild(td);
      });
      tBody.appendChild(tr);
    });
  }

  // ── Utilidades ──────────────────────────────────────────────────────────
  function addMessageToChat(sender, text) {
    const chatContainer = document.getElementById('chat-messages');
    const wrapper = document.createElement('div');
    wrapper.className = `message-wrapper w-full mb-4 ${sender === 'User' ? 'items-end' : 'items-start'}`;

    const bubble = document.createElement('div');
    bubble.className = `chat-message ${sender === 'User' ? 'user' : 'ai'}`;
    bubble.innerText = text;

    wrapper.appendChild(bubble);
    chatContainer.appendChild(wrapper);

    chatContainer.scrollTop = chatContainer.scrollHeight;
    animations.addChatMessage(bubble);
  }

  function parseDrfError(err) {
    if (!err.data || typeof err.data !== 'object') return null;
    const keys = Object.keys(err.data);
    if (!keys.length) return null;
    const first = err.data[keys[0]];
    return Array.isArray(first) ? first[0] : String(first);
  }

  function handleApiError(err, fallback) {
    if (err.status === 401) {
      showToast('Tu sesión expiró. Inicia sesión de nuevo.', 'error');
      forceLogout();
      return;
    }
    showToast(`${fallback} ${parseDrfError(err) || ''}`.trim(), 'error');
  }

  function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.innerText = message;
    toast.className = `fixed bottom-6 right-6 z-[110] max-w-sm px-4 py-3 rounded-xl text-sm font-medium shadow-xl ${
      type === 'error' ? 'bg-red-500/90 text-white' : 'bg-teal text-dark'
    }`;

    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.add('hidden'), 4000);
  }
});
