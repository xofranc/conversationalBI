import { tooltip } from "./shared/chartTooltip.js";
import { scaleOptions } from "./shared/chartScaleOptions.js";

export class ChartBuilder {
  /**
   * Construye un chart basado en la respuesta del backend
   * @param {Object} res - Respuesta del backend{chart_type, chart_config, data}
   * @param {CanvasRenderingContext2D} ctx - Contexto del canvas donde se renderizará el chart
   * @returns {Chart} - Instancia del chart renderizado Chart.js
   */
  build(res, ctx) {
    throw new Error("subclass must implement build()");
  }
  getBaseOptions() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip },
    };
  }
  getScaleOptions() {
    return scaleOptions;
  }
}
