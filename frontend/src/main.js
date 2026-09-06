import "./styles/main.css";
import "./styles/console.css";
import { setupChartDefaults } from "./utils/charts.js";
import { checkSession, enterDashboard } from "./modules/auth.js";
import { loadLibrary, setupUpload } from "./modules/datasetLibrary.js";
import { initChat } from "./modules/chat.js";
import { state } from "./modules/state.js";
import { animations } from "./animations.js";
import { eventBus } from "./lib/eventBus.js";
import { isDemoMode, enterDemoMode } from "./modules/session.js";
import { initDemoBadge } from "./components/demoBadge.js";

// Auto-suscripciones (side effects)
import "./modules/report.js";
import "./modules/history.js";

setupChartDefaults();

function forceLogout() {
  state.datasets = [];
  state.currentDatasetId = null;
  state.figureCount = 0;
  if (state.resultChart) {
    state.resultChart.destroy();
    state.resultChart = null;
  }
  animations.logout();
}

// Suscribirse a SESSION_EXPIRED
eventBus.on('SESSION_EXPIRED', () => forceLogout());

document.addEventListener("DOMContentLoaded", async () => {
  initChat();
  setupUpload();
  initDemoBadge();

  // Detectar si se llego por link /app.html?demo=true
  const urlParams = new URLSearchParams(window.location.search);
  const hasDemoParam = urlParams.get('demo') === 'true';

  // En modo demo, ir directo al dashboard sin login
  if (hasDemoParam || isDemoMode()) {
    // Marcar explicitamente como demo si viene por URL
    if (hasDemoParam) enterDemoMode();

    // Asegurar que auth-view esta oculto y dashboard visible
    const authView = document.getElementById("auth-view");
    const dashboardView = document.getElementById("dashboard-view");
    authView.classList.add("hidden");
    dashboardView.classList.remove("hidden");
    dashboardView.style.opacity = "1";

    loadLibrary();
    return;
  }

  const hasSession = await checkSession();
  if (hasSession) {
    enterDashboard(false, () => loadLibrary());
  }
});
