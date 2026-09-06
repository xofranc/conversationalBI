import { Chart } from "chart.js";
import { ChartBuilder } from "../ChartBuilder.js";

export class ScatterChartBuilder extends ChartBuilder {
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
            backgroundColor: "#0E5E6F",
            pointRadius: 4,
            pointHoverRadius: 5,
          },
        ],
      },
      options: { ...baseOptions, scales: scaleOptions },
    };
  }
}
