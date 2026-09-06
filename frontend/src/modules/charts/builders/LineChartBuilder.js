import { Chart } from "chart.js";
import { ChartBuilder } from "../ChartBuilder.js";

export class LineChartBuilder extends ChartBuilder {
  build(res, ctx) {
    return new Chart(ctx, this.getConfig(res));
  }

  getConfig(res) {
    const cfg = res.chart_config || {};
    const baseOptions = this.getBaseOptions();
    const scaleOptions = this.getScaleOptions();

    return {
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
    };
  }
}
