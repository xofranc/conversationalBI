import { Chart } from "chart.js";
import { ChartBuilder } from "../ChartBuilder.js";

export class AnomalyChartBuilder extends ChartBuilder {
  build(res, ctx) {
    return new Chart(ctx, this.getConfig(res));
  }

  getConfig(res) {
    const cfg = res.chart_config || {};
    const baseOptions = this.getBaseOptions();
    const scaleOptions = this.getScaleOptions();

    return {
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
    };
  }
}
