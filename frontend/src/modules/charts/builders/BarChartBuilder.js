import { Chart } from "chart.js";
import { ChartBuilder } from "../ChartBuilder.js";

export class BarChartBuilder extends ChartBuilder {
  build(res, ctx) {
    return new Chart(ctx, this.getConfig(res));
  }

  getConfig(res) {
    const cfg = res.chart_config || {};
    const baseOptions = this.getBaseOptions();
    const scaleOptions = this.getScaleOptions();

    return {
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
    };
  }
}
