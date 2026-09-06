import { chartRegistry } from "./charts/ChartRegistry.js";

export function renderChart(res) {
  const container = document.getElementById("chart-container");

  if (!container) return null;

  container.classList.remove("hidden");

  if (res.chart_type === "table" || !res.data?.length) {
    container.classList.add("hidden");
    return null;
  }

  const ctx = document.getElementById("chart-1").getContext("2d");
  return chartRegistry.render(res, ctx);
}
