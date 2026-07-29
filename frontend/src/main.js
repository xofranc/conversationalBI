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

Chart.defaults.font.family = '"Inter", system-ui, sans-serif';
Chart.defaults.color = '#5C6672';

// App State
let datasets = [];
let currentDatasetId = null;
let resultChart = null;
let sending = false;
let toastTimer = null;
let figureCount = 0;

const CHART_COLORS = ['#0E5E6F', '#3E8FA3', '#8FC0C9', '#C77B21', '#5C6672', '#B3402E'];
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

  // Sesión activa → directo a la consola
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
    datasets = [];
    currentDatasetId = null;
    renderDatasetList();
    renderHistory([]);
    resetReport(true);
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
    loadLibrary();
  }

  // ── Biblioteca de fuentes de datos ──────────────────────────────────────
  async function loadLibrary(selectId = null) {
    try {
      const list = await api.dataset.list();
      datasets = Array.isArray(list) ? list : (list.results || []);
    } catch {
      datasets = [];
    }

    if (selectId && datasets.some((d) => d.id === selectId)) {
      currentDatasetId = selectId;
    } else if (!currentDatasetId || !datasets.some((d) => d.id === currentDatasetId)) {
      const firstReady = datasets.find((d) => d.status === 'ready');
      currentDatasetId = firstReady ? firstReady.id : null;
    }

    renderDatasetList();
    syncDatasetLabels();
    loadHistory();
  }

  function activeDataset() {
    return datasets.find((d) => d.id === currentDatasetId) || null;
  }

  function syncDatasetLabels() {
    const ds = activeDataset();
    const label = ds ? ds.name : 'sin fuente';
    document.getElementById('masthead-dataset').innerText = label;
    document.getElementById('chat-dataset').innerText = ds ? ds.name : 'sin fuente activa';
  }

  function renderDatasetList() {
    const list = document.getElementById('dataset-list');
    document.getElementById('dataset-count').innerText = String(datasets.length);
    list.innerHTML = '';

    datasets.forEach((ds) => {
      const li = document.createElement('li');
      const item = document.createElement('button');
      item.type = 'button';
      item.className = `dataset-item${ds.id === currentDatasetId ? ' active' : ''}`;

      const meta = ds.status === 'ready'
        ? `${Number(ds.row_count).toLocaleString('es-CO')} filas`
        : ds.status;

      const dot = document.createElement('span');
      dot.className = 'd-dot';
      const name = document.createElement('span');
      name.className = 'd-name';
      name.innerText = ds.name;
      const metaEl = document.createElement('span');
      metaEl.className = 'd-meta';
      metaEl.innerText = meta;
      const del = document.createElement('span');
      del.className = 'd-delete';
      del.innerText = '×';
      del.title = `Eliminar ${ds.name}`;

      item.append(dot, name, metaEl, del);
      item.addEventListener('click', () => selectDataset(ds.id));
      del.addEventListener('click', (e) => {
        e.stopPropagation();
        removeDataset(ds.id);
      });

      li.appendChild(item);
      list.appendChild(li);
    });
  }

  function selectDataset(id) {
    if (id === currentDatasetId) return;
    currentDatasetId = id;
    renderDatasetList();
    syncDatasetLabels();
    resetReport(true);
    const ds = activeDataset();
    if (ds) {
      addMessageToChat('AI', `Fuente activa: "${ds.name}" (${Number(ds.row_count).toLocaleString('es-CO')} filas). ¿Qué quieres saber?`);
    }
    loadHistory();
  }

  async function removeDataset(id) {
    try {
      await api.dataset.delete(id);
    } catch {
      // Si ya no existe en el backend, igual se desvincula localmente
    }
    const wasActive = id === currentDatasetId;
    datasets = datasets.filter((d) => d.id !== id);
    if (wasActive) {
      currentDatasetId = null;
      const firstReady = datasets.find((d) => d.status === 'ready');
      currentDatasetId = firstReady ? firstReady.id : null;
      resetReport(true);
    }
    renderDatasetList();
    syncDatasetLabels();
    loadHistory();
    showToast('Fuente de datos eliminada.', 'success');
  }

  // ── Bitácora de consultas ───────────────────────────────────────────────
  async function loadHistory() {
    if (!currentDatasetId) {
      renderHistory([]);
      return;
    }
    try {
      const data = await api.query.history(currentDatasetId);
      renderHistory(data.results || data || []);
    } catch {
      // La bitácora es secundaria: un fallo aquí no interrumpe la consola
    }
  }

  function renderHistory(items) {
    const list = document.getElementById('history-list');
    const empty = document.getElementById('history-empty');
    list.innerHTML = '';
    empty.classList.toggle('hidden', items.length > 0);

    items.forEach((q) => {
      const li = document.createElement('li');
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'history-item';
      btn.title = q.question;

      const time = new Date(q.created_at).toLocaleTimeString('es-CO', {
        hour: '2-digit', minute: '2-digit',
      });
      const status = !q.success ? 'fail' : q.cached ? 'cache' : 'ok';

      const timeEl = document.createElement('span');
      timeEl.className = 'h-time';
      timeEl.innerText = time;
      const qEl = document.createElement('span');
      qEl.className = 'h-q';
      qEl.innerText = q.question;
      const statusEl = document.createElement('span');
      statusEl.className = `h-status ${status}`;

      btn.append(timeEl, qEl, statusEl);
      btn.addEventListener('click', () => openHistoryQuery(q.id));
      li.appendChild(btn);
      list.appendChild(li);
    });
  }

  async function openHistoryQuery(id) {
    try {
      const q = await api.query.detail(id);
      if (!q.success || !q.result) {
        showToast('Esa consulta no tiene resultado guardado.', 'error');
        return;
      }
      renderResult({
        success: q.success,
        error_msg: q.error_msg,
        sql: q.sql_generated,
        execution_time: q.execution_time,
        model_used: q.model_used,
        cached: q.cached,
        data: q.result.result_json,
        columns: q.result.columns,
        chart_type: q.result.chart_type,
        chart_config: q.result.chart_config,
        row_count: q.result.row_count,
      }, q.question);
      addMessageToChat('AI', q.result.answer || `${q.result.row_count} fila(s) encontradas.`, {
        sql: q.sql_generated,
        execution_time: q.execution_time,
        cached: q.cached,
        model_used: q.model_used,
      });
      showToast('Consulta restaurada de la bitácora.', 'success');
    } catch (err) {
      handleApiError(err, 'No se pudo abrir la consulta.');
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
    dropZone.classList.add('border-petrol-bright', 'bg-rail-raise');
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('border-petrol-bright', 'bg-rail-raise');
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('border-petrol-bright', 'bg-rail-raise');
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

      resetReport(true);
      addMessageToChat(
        'AI',
        `Fuente "${dataset.name}" lista: ${dataset.row_count} filas y ${dataset.column_count} columnas. ¿Qué quieres saber?`
      );
      await loadLibrary(dataset.id);
    } catch (err) {
      handleApiError(err, 'Error al cargar el archivo.');
    } finally {
      animations.hideLoader();
      fileInput.value = '';
    }
  }

  // Sin fuente no hay informe: se retira el documento
  function resetReport(clearChat) {
    if (resultChart) {
      resultChart.destroy();
      resultChart = null;
    }
    figureCount = 0;
    const emptyState = document.getElementById('empty-state');
    document.getElementById('dashboard-content').classList.add('hidden');
    emptyState.classList.remove('hidden');
    emptyState.style.opacity = '';
    emptyState.style.transform = '';
    document.getElementById('masthead-folio').innerText = '—';
    if (clearChat) {
      document.getElementById('chat-messages').innerHTML = '';
    }
  }

  // ── Chat ────────────────────────────────────────────────────────────────
  const sendMessage = async () => {
    const text = chatInput.value.trim();
    if (text.length < 5) {
      showToast('La pregunta debe tener al menos 5 caracteres.', 'error');
      return;
    }
    if (!currentDatasetId) {
      showToast('Por favor, sube o activa una fuente de datos primero.', 'error');
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
        addMessageToChat('AI', res.answer || `${res.row_count} fila(s) encontradas.`, {
          sql: res.sql,
          execution_time: res.execution_time,
          cached: res.cached,
          model_used: res.model_used,
        });
        renderResult(res, text);
        loadHistory();
      } else {
        addMessageToChat(
          'AI',
          `No pude responder esa pregunta: ${res.error_msg || 'error desconocido'}.`,
          null,
          res.suggestions || []
        );
        loadHistory();
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

  // Chips de ejemplo: la pantalla vacía invita a actuar
  document.querySelectorAll('.example-chip').forEach((chip) => {
    chip.addEventListener('click', () => {
      chatInput.value = chip.dataset.question;
      chatInput.focus();
    });
  });

  // ── Render del informe ──────────────────────────────────────────────────
  function renderResult(res, question) {
    animations.revealChart();

    const rows = Number(res.row_count);
    document.getElementById('kpi-rows').innerText = Number.isFinite(rows)
      ? rows.toLocaleString('es-CO')
      : res.row_count;
    const seconds = Number(res.execution_time);
    document.getElementById('kpi-time').innerText = Number.isFinite(seconds)
      ? `${seconds.toFixed(2)}s`
      : `${res.execution_time}s`;
    document.getElementById('kpi-source').innerText = res.cached ? 'caché' : (res.model_used || 'IA');
    document.getElementById('masthead-folio').innerText = formatFolio();

    figureCount += 1;
    document.getElementById('figure-label').innerText = `fig. ${figureCount}`;
    document.getElementById('figure-title').innerText = question;
    document.getElementById('annex-caption').innerText =
      res.data.length > MAX_TABLE_ROWS
        ? `Datos del resultado · primeras ${MAX_TABLE_ROWS} de ${res.data.length} filas`
        : 'Datos del resultado';

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

    // Tooltip con acabado de consola: papel, tinta y filete
    const tooltip = {
      backgroundColor: '#FFFFFF',
      titleColor: '#1B2430',
      bodyColor: '#1B2430',
      borderColor: '#DCE0D9',
      borderWidth: 1,
      padding: 10,
      displayColors: false,
      titleFont: { family: '"JetBrains Mono", ui-monospace, monospace', size: 11 },
      bodyFont: { family: '"JetBrains Mono", ui-monospace, monospace', size: 12 },
    };

    // Serie única: la leyenda no informa, se oculta
    const baseOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip },
    };

    const scaleOptions = {
      y: { ticks: { color: '#5C6672' }, grid: { color: 'rgba(27, 36, 48, 0.07)' } },
      x: { ticks: { color: '#5C6672' }, grid: { color: 'rgba(27, 36, 48, 0.07)' } },
    };

    if (res.chart_type === 'pie') {
      resultChart = new Chart(ctx, {
        type: 'pie',
        data: {
          labels: res.data.map((r) => r[cfg.nameKey]),
          datasets: [{
            data: res.data.map((r) => r[cfg.valueKey]),
            backgroundColor: CHART_COLORS,
            borderColor: '#FFFFFF',
            borderWidth: 2,
          }],
        },
        options: {
          ...baseOptions,
          plugins: {
            legend: {
              display: true,
              position: 'bottom',
              labels: { color: '#1B2430', boxWidth: 12, boxHeight: 12, padding: 16, font: { size: 11 } },
            },
            tooltip,
          },
        },
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
            backgroundColor: '#0E5E6F',
            pointRadius: 4,
            pointHoverRadius: 5,
          }],
        },
        options: { ...baseOptions, scales: scaleOptions },
      });
      return;
    }

    if (res.chart_type === 'line') {
      resultChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: res.data.map((r) => r[cfg.xKey]),
          datasets: [{
            label: cfg.yKey,
            data: res.data.map((r) => r[cfg.yKey]),
            borderColor: '#0E5E6F',
            backgroundColor: 'rgba(14, 94, 111, 0.10)',
            fill: true,
            tension: 0.35,
            borderWidth: 2,
            pointRadius: 3,
            pointBackgroundColor: '#0E5E6F',
            pointBorderColor: '#FFFFFF',
            pointBorderWidth: 1.5,
          }],
        },
        options: { ...baseOptions, scales: scaleOptions },
      });
      return;
    }

    // ── Análisis avanzados ──────────────────────────────────────────────
    if (res.chart_type === 'forecast') {
      const labels = res.data.map((r) => r[cfg.xKey]);
      const real = res.data.map((r) => (r[cfg.splitKey] === 'real' ? r[cfg.yKey] : null));
      const pred = res.data.map((r) => (r[cfg.splitKey] === 'real' ? null : r[cfg.yKey]));
      const lower = res.data.map((r) => r.inferior ?? null);
      const upper = res.data.map((r) => r.superior ?? null);

      // Ancla: la línea de pronóstico arranca del último punto real
      const firstPred = res.data.findIndex((r) => r[cfg.splitKey] !== 'real');
      if (firstPred > 0) pred[firstPred - 1] = real[firstPred - 1];

      resultChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels,
          datasets: [
            // Banda de confianza: inferior + superior con relleno entre ambas
            { label: 'inferior', data: lower, borderWidth: 0, pointRadius: 0, spanGaps: true },
            {
              label: 'superior', data: upper, borderWidth: 0, pointRadius: 0, spanGaps: true,
              fill: '-1', backgroundColor: 'rgba(199, 123, 33, 0.12)',
            },
            {
              label: 'Real', data: real, borderColor: '#0E5E6F', backgroundColor: '#0E5E6F',
              tension: 0.3, borderWidth: 2, pointRadius: 2.5,
              pointBorderColor: '#FFFFFF', pointBorderWidth: 1.5,
            },
            {
              label: 'Pronóstico', data: pred, borderColor: '#C77B21', backgroundColor: '#C77B21',
              borderDash: [6, 4], tension: 0.3, borderWidth: 2, pointRadius: 3.5, pointStyle: 'rectRot',
              pointBorderColor: '#FFFFFF', pointBorderWidth: 1.5,
            },
          ],
        },
        options: {
          ...baseOptions,
          plugins: {
            legend: {
              display: true, position: 'bottom',
              labels: {
                color: '#1B2430', boxWidth: 12, boxHeight: 12, padding: 16, font: { size: 11 },
                filter: (item) => item.text === 'Real' || item.text === 'Pronóstico',
              },
            },
            tooltip: { ...tooltip, filter: (t) => t.datasetIndex >= 2 },
          },
          scales: scaleOptions,
        },
      });
      return;
    }

    if (res.chart_type === 'anomaly') {
      resultChart = new Chart(ctx, {
        type: 'scatter',
        data: {
          datasets: [{
            label: `${cfg.xKey} vs ${cfg.yKey}`,
            data: res.data.map((r) => ({ x: r[cfg.xKey], y: r[cfg.yKey] })),
            backgroundColor: '#C77B21',
            borderColor: '#FFFFFF',
            borderWidth: 1.5,
            pointRadius: 6,
            pointHoverRadius: 7,
          }],
        },
        options: { ...baseOptions, scales: scaleOptions },
      });
      return;
    }

    if (res.chart_type === 'segment') {
      const segKey = cfg.segmentKey || 'segmento';
      const grupos = [...new Set(res.data.map((r) => r[segKey]))].sort();
      resultChart = new Chart(ctx, {
        type: 'scatter',
        data: {
          datasets: grupos.map((g, i) => ({
            label: g,
            data: res.data.filter((r) => r[segKey] === g).map((r) => ({ x: r[cfg.xKey], y: r[cfg.yKey] })),
            backgroundColor: CHART_COLORS[i % CHART_COLORS.length],
            pointRadius: 4,
            pointHoverRadius: 5,
          })),
        },
        options: {
          ...baseOptions,
          plugins: {
            legend: {
              display: true, position: 'bottom',
              labels: { color: '#1B2430', boxWidth: 12, boxHeight: 12, padding: 16, font: { size: 11 } },
            },
            tooltip,
          },
          scales: scaleOptions,
        },
      });
      return;
    }

    if (res.chart_type === 'drivers') {
      resultChart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: res.data.map((r) => r[cfg.yKey]),   // factor
          datasets: [{
            label: cfg.xKey,                           // correlación
            data: res.data.map((r) => r[cfg.xKey]),
            backgroundColor: res.data.map((r) => (r[cfg.xKey] >= 0 ? '#0E5E6F' : '#C77B21')),
            hoverBackgroundColor: res.data.map((r) => (r[cfg.xKey] >= 0 ? '#0A4A58' : '#A8661B')),
            borderRadius: 5,
            maxBarThickness: 28,
          }],
        },
        options: { ...baseOptions, indexAxis: 'y', scales: scaleOptions },
      });
      return;
    }

    // bar
    resultChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: res.data.map((r) => r[cfg.xKey]),
        datasets: [{
          label: cfg.yKey,
          data: res.data.map((r) => r[cfg.yKey]),
          backgroundColor: '#0E5E6F',
          hoverBackgroundColor: '#0A4A58',
          borderRadius: 5,
          maxBarThickness: 52,
        }],
      },
      options: { ...baseOptions, scales: scaleOptions },
    });
  }

  function renderTable(res) {
    const tHead = document.getElementById('table-head');
    const tBody = document.getElementById('table-body');
    tHead.innerHTML = '';
    tBody.innerHTML = '';

    const cols = (res.columns?.length ? res.columns.map((c) => c.name) : Object.keys(res.data?.[0] || {}));
    const rows = res.data.slice(0, MAX_TABLE_ROWS);

    // Columnas numéricas: a la derecha y con cifras tabulares, como en un anexo real
    const numericCols = new Set(
      cols.filter(
        (col) =>
          rows.length > 0 &&
          rows.every((r) => r[col] === null || r[col] === undefined || typeof r[col] === 'number')
      )
    );

    cols.forEach((col) => {
      const th = document.createElement('th');
      th.className = `px-5 py-3 font-medium${numericCols.has(col) ? ' text-right' : ''}`;
      th.innerText = col;
      tHead.appendChild(th);
    });

    rows.forEach((row) => {
      const tr = document.createElement('tr');
      cols.forEach((col) => {
        const td = document.createElement('td');
        const isNum = numericCols.has(col);
        td.className = `px-5 py-3 whitespace-nowrap font-mono text-[0.8rem] tabular-nums${isNum ? ' text-right' : ''}`;
        const val = row[col];
        td.innerText = val === null || val === undefined
          ? '—'
          : isNum
            ? Number(val).toLocaleString('es-CO')
            : val;
        tr.appendChild(td);
      });
      tBody.appendChild(tr);
    });
  }

  // ── Utilidades ──────────────────────────────────────────────────────────
  function formatFolio() {
    const now = new Date();
    const fecha = now.toLocaleDateString('es-CO', { day: 'numeric', month: 'short', year: 'numeric' });
    const hora = now.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' });
    return `actualizado ${fecha} · ${hora}`;
  }

  function addMessageToChat(sender, text, receipt = null, suggestions = []) {
    const chatContainer = document.getElementById('chat-messages');
    const wrapper = document.createElement('div');
    wrapper.className = `message-wrapper w-full mb-4 ${sender === 'User' ? 'items-end' : 'items-start'}`;

    const bubble = document.createElement('div');
    bubble.className = `chat-message ${sender === 'User' ? 'user' : 'ai'}`;
    bubble.innerText = text;
    wrapper.appendChild(bubble);

    // El recibo: la firma de verificabilidad del producto
    if (receipt?.sql) {
      const details = document.createElement('details');
      details.className = 'sql-receipt';

      const summary = document.createElement('summary');
      const label = document.createElement('span');
      label.innerText = `recibo · ${receipt.execution_time}s`;
      summary.appendChild(label);

      if (receipt.cached) {
        const badge = document.createElement('span');
        badge.className = 'sql-badge cache';
        badge.innerText = 'caché';
        summary.appendChild(badge);
      } else if (receipt.model_used) {
        const badge = document.createElement('span');
        badge.className = 'sql-badge model';
        badge.innerText = receipt.model_used;
        summary.appendChild(badge);
      }

      const pre = document.createElement('pre');
      pre.innerText = receipt.sql;

      details.appendChild(summary);
      details.appendChild(pre);
      wrapper.appendChild(details);
    }

    // Caminos cuando la respuesta falló: la conversación no muere
    if (suggestions.length) {
      const hint = document.createElement('p');
      hint.className = 'suggestion-hint';
      hint.innerText = 'Prueba con:';
      wrapper.appendChild(hint);

      const chips = document.createElement('div');
      chips.className = 'suggestion-chips';
      suggestions.forEach((s) => {
        const chip = document.createElement('button');
        chip.type = 'button';
        chip.className = 'example-chip';
        chip.innerText = s;
        chip.addEventListener('click', () => {
          chatInput.value = s;
          chatInput.focus();
        });
        chips.appendChild(chip);
      });
      wrapper.appendChild(chips);
    }

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
    toast.className = `fixed bottom-6 right-6 z-[110] max-w-sm px-4 py-3 rounded-xl text-sm font-medium shadow-lift ${
      type === 'error' ? 'bg-danger text-white' : 'bg-rail text-white'
    }`;

    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.add('hidden'), 4000);
  }
});
