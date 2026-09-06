import { Chart } from "chart.js";
import { CHART_COLORS } from "../../../config/constants.js";
import { ChartBuilder } from "../ChartBuilder.js";

export class PieChartBuilder extends ChartBuilder {
  build(res, ctx) {
    return new Chart(ctx, this.getConfig(res));
  }

  getConfig(res) {
    const cfg = res.chart_config || {};
    const baseOptions = this.getBaseOptions();

    return {
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
          tooltip: baseOptions.plugins.tooltip,
        },
      },
    };
  }
}
