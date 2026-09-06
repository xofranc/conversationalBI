import { Chart } from "chart.js";
import { ChartBuilder } from "../ChartBuilder.js";

export class ForecastChartBuilder extends ChartBuilder {
  build(res, ctx) {
    return new Chart(ctx, this.getConfig(res));
  }

  getConfig(res) {
    const cfg = res.chart_config || {};
    const baseOptions = this.getBaseOptions();
    const scaleOptions = this.getScaleOptions();

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

    return {
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
          tooltip: { ...baseOptions.plugins.tooltip, filter: (t) => t.datasetIndex >= 2 },
        },
        scales: scaleOptions,
      },
    };
  }
}
