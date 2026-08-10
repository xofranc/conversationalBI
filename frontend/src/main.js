import "./styles/main.css";
import "./styles/console.css";
import { setupChartDefaults } from "./utils/charts.js";
import { checkSession, setupAuth, enterDashboard } from "./modules/auth.js";
import {
  initDatasetLibrary,
  loadLibrary,
  setupUpload,
} from "./modules/datasetLibrary.js";
import { initHistory, loadHistory } from "./modules/history.js";
import { initChat, addMessageToChat } from "./modules/chat.js";
import { renderResult, resetReport } from "./modules/report.js";
import { state } from "./modules/state.js";
import { animations } from "./animations.js";

setupChartDefaults();

document.addEventListener("DOMContentLoaded", async () => {
  initDatasetLibrary({
    onSelect: (ds) => {
      resetReport(true);
      if (ds) {
        addMessageToChat(
          "AI",
          `Fuente activa: "${ds.name}" (${Number(ds.row_count).toLocaleString("es-CO")} filas). ¿Qué quieres saber?`,
        );
      }
      loadHistory();
    },
    onRemove: (wasActive) => {
      if (wasActive) {
        resetReport(true);
      }
      loadHistory();
    },
    onUpload: (dataset) => {
      resetReport(true);
      addMessageToChat(
        "AI",
        `Fuente "${dataset.name}" lista: ${dataset.row_count} filas y ${dataset.column_count} columnas. ¿Qué quieres saber?`,
      );
      loadLibrary(dataset.id);
    },
  });

  initHistory({
    onRestore: (q) => {
      renderResult(
        {
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
        },
        q.question,
      );
      addMessageToChat(
        "AI",
        q.result.answer || `${q.result.row_count} fila(s) encontradas.`,
        {
          sql: q.sql_generated,
          execution_time: q.execution_time,
          cached: q.cached,
          model_used: q.model_used,
        },
      );
    },
  });

  initChat({
    onResult: (res, question) => {
      renderResult(res, question);
    },
    onHistoryUpdate: () => {
      loadHistory();
    },
    onSessionExpired: () => {
      forceLogout();
    },
  });

  setupAuth({
    onEnter: () => loadLibrary(),
    onLeave: () => forceLogout(),
  });

  setupUpload();

  // Sesión activa → directo a la consola
  const hasSession = await checkSession();
  if (hasSession) {
    enterDashboard(false, () => loadLibrary());
  }
});

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
