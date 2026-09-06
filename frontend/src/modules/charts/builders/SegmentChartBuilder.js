import { Chart } from "chart.js";
import { CHART_COLORS } from "../../../config/constants.js";
import { ChartBuilder } from "../ChartBuilder.js";

export class SegmentChartBuilder extends ChartBuilder {
  build(res, ctx) {
    return new Chart(ctx, this.getConfig(res));
  }

  getConfig(res) {
    const cfg = res.chart_config || {};
    const baseOptions = this.getBaseOptions();
    const scaleOptions = this.getScaleOptions();
    const segKey = cfg.segmentKey || "segmento";
    const grupos = [...new Set(res.data.map((r) => r[segKey]))].sort();

    return {
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
          tooltip: baseOptions.plugins.tooltip,
        },
        scales: scaleOptions,
      },
    };
  }
}
