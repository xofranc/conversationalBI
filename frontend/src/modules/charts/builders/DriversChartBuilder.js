import { Chart } from "chart.js";
import { ChartBuilder } from "../ChartBuilder.js";

export class DriversChartBuilder extends ChartBuilder {
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
    };
  }
}
