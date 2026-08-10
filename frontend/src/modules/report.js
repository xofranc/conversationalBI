import { state } from "./state.js";
import { animations } from "../animations.js";
import { formatFolio } from "../utils/format.js";
import { MAX_TABLE_ROWS } from "../config/constants.js";
import { renderChart } from "./resultChart.js";
import { renderTable } from "./reportTable.js";

export function resetReport(clearChat) {
  if (state.resultChart) {
    state.resultChart.destroy();
    state.resultChart = null;
  }
  state.figureCount = 0;
  const emptyState = document.getElementById("empty-state");
  const dashboardContent = document.getElementById("dashboard-content");
  dashboardContent.classList.add("hidden");
  emptyState.classList.remove("hidden");
  emptyState.style.opacity = "";
  emptyState.style.transform = "";
  document.getElementById("masthead-folio").innerText = "—";
  if (clearChat) {
    document.getElementById("chat-messages").innerHTML = "";
  }
}

export function renderResult(res, question) {
  animations.revealChart();

  const rows = Number(res.row_count);
  document.getElementById("kpi-rows").innerText = Number.isFinite(rows)
    ? rows.toLocaleString("es-CO")
    : res.row_count;
  const seconds = Number(res.execution_time);
  document.getElementById("kpi-time").innerText = Number.isFinite(seconds)
    ? `${seconds.toFixed(2)}s`
    : `${res.execution_time}s`;
  document.getElementById("kpi-source").innerText = res.cached
    ? "caché"
    : res.model_used || "IA";
  document.getElementById("masthead-folio").innerText = formatFolio();

  state.figureCount += 1;
  document.getElementById("figure-label").innerText =
    `fig. ${state.figureCount}`;
  document.getElementById("figure-title").innerText = question;
  document.getElementById("annex-caption").innerText =
    res.data.length > MAX_TABLE_ROWS
      ? `Datos del resultado · primeras ${MAX_TABLE_ROWS} de ${res.data.length} filas`
      : "Datos del resultado";

  state.resultChart = renderChart(res);
  renderTable(res);
}
