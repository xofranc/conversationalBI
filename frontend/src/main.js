import "./styles/main.css";
import "./styles/console.css";
import { setupChartDefaults } from "./utils/charts.js";
import { checkSession, enterDashboard } from "./modules/auth.js";
import { loadLibrary, setupUpload } from "./modules/datasetLibrary.js";
import { initChat } from "./modules/chat.js";
import { state } from "./modules/state.js";
import { animations } from "./animations.js";
import { eventBus } from "./lib/eventBus.js";
import { isDemoMode } from "./modules/session.js";
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

  // En modo demo, ir directo al dashboard sin login
  if (isDemoMode()) {
    enterDashboard(false, () => loadLibrary());
    return;
  }

  const hasSession = await checkSession();
  if (hasSession) {
    enterDashboard(false, () => loadLibrary());
  }
});
