import { Chart } from "chart.js";
import { CHART_COLORS } from "../config/constants.js";

export function renderChart(res) {
  const container = document.getElementById("chart-container");

  if (!container) return null;

  container.classList.remove("hidden");
  const cfg = res.chart_config || {};
  const ctx = document.getElementById("chart-1").getContext("2d");

  const tooltip = {
    backgroundColor: "#FFFFFF",
    titleColor: "#1B2430",
    bodyColor: "#1B2430",
    borderColor: "#DCE0D9",
    borderWidth: 1,
    padding: 10,
    displayColors: false,
    titleFont: {
      family: '"JetBrains Mono", ui-monospace, monospace',
      size: 11,
    },
    bodyFont: {
      family: '"JetBrains Mono", ui-monospace, monospace',
      size: 12,
    },
  };

  const baseOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip },
  };

  const scaleOptions = {
    y: {
      ticks: { color: "#5C6672" },
      grid: { color: "rgba(27, 36, 48, 0.07)" },
    },
    x: {
      ticks: { color: "#5C6672" },
      grid: { color: "rgba(27, 36, 48, 0.07)" },
    },
  };

  if (res.chart_type === "table" || !res.data?.length) {
    container.classList.add("hidden");
    return null;
  }

  if (res.chart_type === "pie") {
    return new Chart(ctx, {
      type: "pie",
      data: {
        labels: res.data.map((r) => r[cfg.nameKey]),
        datasets: [
          {
            data: res.data.map((r) => r[cfg.valueKey]),
            backgroundColor: CHART_COLORS,
            borderColor: "#FFFFFF",
            borderWidth: 2,
          },
        ],
      },
      options: {
        ...baseOptions,
        plugins: {
          legend: {
            display: true,
            position: "bottom",
            labels: {
              color: "#1B2430",
              boxWidth: 12,
              boxHeight: 12,
              padding: 16,
              font: { size: 11 },
            },
          },
          tooltip,
        },
      },
    });
  }

  if (res.chart_type === "scatter") {
    return new Chart(ctx, {
      type: "scatter",
      data: {
        datasets: [
          {
            label: `${cfg.xKey} vs ${cfg.yKey}`,
            data: res.data.map((r) => ({ x: r[cfg.xKey], y: r[cfg.yKey] })),
            backgroundColor: "#0E5E6F",
            pointRadius: 4,
            pointHoverRadius: 5,
          },
        ],
      },
      options: { ...baseOptions, scales: scaleOptions },
    });
  }

  if (res.chart_type === "line") {
    return new Chart(ctx, {
      type: "line",
      data: {
        labels: res.data.map((r) => r[cfg.xKey]),
        datasets: [
          {
            label: cfg.yKey,
            data: res.data.map((r) => r[cfg.yKey]),
            borderColor: "#0E5E6F",
            backgroundColor: "rgba(14, 94, 111, 0.10)",
            fill: true,
            tension: 0.35,
            borderWidth: 2,
            pointRadius: 3,
            pointBackgroundColor: "#0E5E6F",
            pointBorderColor: "#FFFFFF",
            pointBorderWidth: 1.5,
          },
        ],
      },
      options: { ...baseOptions, scales: scaleOptions },
    });
  }

  if (res.chart_type === "forecast") {
    const labels = res.data.map((r) => r[cfg.xKey]);
    const real = res.data.map((r) =>
      r[cfg.splitKey] === "real" ? r[cfg.yKey] : null,
    );
    const pred = res.data.map((r) =>
      r[cfg.splitKey] === "real" ? null : r[cfg.yKey],
    );
    const lower = res.data.map((r) => r.inferior ?? null);
    const upper = res.data.map((r) => r.superior ?? null);

    const firstPred = res.data.findIndex((r) => r[cfg.splitKey] !== "real");
    if (firstPred > 0) pred[firstPred - 1] = real[firstPred - 1];

    return new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "inferior",
            data: lower,
            borderWidth: 0,
            pointRadius: 0,
            spanGaps: true,
          },
          {
            label: "superior",
            data: upper,
            borderWidth: 0,
            pointRadius: 0,
            spanGaps: true,
            fill: "-1",
            backgroundColor: "rgba(199, 123, 33, 0.12)",
          },
          {
            label: "Real",
            data: real,
            borderColor: "#0E5E6F",
            backgroundColor: "#0E5E6F",
            tension: 0.3,
            borderWidth: 2,
            pointRadius: 2.5,
            pointBorderColor: "#FFFFFF",
            pointBorderWidth: 1.5,
          },
          {
            label: "Pronóstico",
            data: pred,
            borderColor: "#C77B21",
            backgroundColor: "#C77B21",
            borderDash: [6, 4],
            tension: 0.3,
            borderWidth: 2,
            pointRadius: 3.5,
            pointStyle: "rectRot",
            pointBorderColor: "#FFFFFF",
            pointBorderWidth: 1.5,
          },
        ],
      },
      options: {
        ...baseOptions,
        plugins: {
          legend: {
            display: true,
            position: "bottom",
            labels: {
              color: "#1B2430",
              boxWidth: 12,
              boxHeight: 12,
              padding: 16,
              font: { size: 11 },
              filter: (item) =>
                item.text === "Real" || item.text === "Pronóstico",
            },
          },
          tooltip: { ...tooltip, filter: (t) => t.datasetIndex >= 2 },
        },
        scales: scaleOptions,
      },
    });
  }

  if (res.chart_type === "anomaly") {
    return new Chart(ctx, {
      type: "scatter",
      data: {
        datasets: [
          {
            label: `${cfg.xKey} vs ${cfg.yKey}`,
            data: res.data.map((r) => ({ x: r[cfg.xKey], y: r[cfg.yKey] })),
            backgroundColor: "#C77B21",
            borderColor: "#FFFFFF",
            borderWidth: 1.5,
            pointRadius: 6,
            pointHoverRadius: 7,
          },
        ],
      },
      options: { ...baseOptions, scales: scaleOptions },
    });
  }

  if (res.chart_type === "segment") {
    const segKey = cfg.segmentKey || "segmento";
    const grupos = [...new Set(res.data.map((r) => r[segKey]))].sort();
    return new Chart(ctx, {
      type: "scatter",
      data: {
        datasets: grupos.map((g, i) => ({
          label: g,
          data: res.data
            .filter((r) => r[segKey] === g)
            .map((r) => ({ x: r[cfg.xKey], y: r[cfg.yKey] })),
          backgroundColor: CHART_COLORS[i % CHART_COLORS.length],
          pointRadius: 4,
          pointHoverRadius: 5,
        })),
      },
      options: {
        ...baseOptions,
        plugins: {
          legend: {
            display: true,
            position: "bottom",
            labels: {
              color: "#1B2430",
              boxWidth: 12,
              boxHeight: 12,
              padding: 16,
              font: { size: 11 },
            },
          },
          tooltip,
        },
        scales: scaleOptions,
      },
    });
  }

  if (res.chart_type === "drivers") {
    return new Chart(ctx, {
      type: "bar",
      data: {
        labels: res.data.map((r) => r[cfg.yKey]),
        datasets: [
          {
            label: cfg.xKey,
            data: res.data.map((r) => r[cfg.xKey]),
            backgroundColor: res.data.map((r) =>
              r[cfg.xKey] >= 0 ? "#0E5E6F" : "#C77B21",
            ),
            hoverBackgroundColor: res.data.map((r) =>
              r[cfg.xKey] >= 0 ? "#0A4A58" : "#A8661B",
            ),
            borderRadius: 5,
            maxBarThickness: 28,
          },
        ],
      },
      options: { ...baseOptions, indexAxis: "y", scales: scaleOptions },
    });
  }

  // bar (default)
  return new Chart(ctx, {
    type: "bar",
    data: {
      labels: res.data.map((r) => r[cfg.xKey]),
      datasets: [
        {
          label: cfg.yKey,
          data: res.data.map((r) => r[cfg.yKey]),
          backgroundColor: "#0E5E6F",
          hoverBackgroundColor: "#0A4A58",
          borderRadius: 5,
          maxBarThickness: 52,
        },
      ],
    },
    options: { ...baseOptions, scales: scaleOptions },
  });
}
