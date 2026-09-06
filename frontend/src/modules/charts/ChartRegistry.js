import { PieChartBuilder } from "./builders/PieChartBuilder.js";
import { ScatterChartBuilder } from "./builders/ScatterChartBuilder.js";
import { LineChartBuilder } from "./builders/LineChartBuilder.js";
import { ForecastChartBuilder } from "./builders/ForecastChartBuilder.js";
import { AnomalyChartBuilder } from "./builders/AnomalyChartBuilder.js";
import { SegmentChartBuilder } from "./builders/SegmentChartBuilder.js";
import { DriversChartBuilder } from "./builders/DriversChartBuilder.js";
import { BarChartBuilder } from "./builders/BarChartBuilder.js";

class ChartRegistry {
  constructor() {
    this.builders = new Map();
    this.register("pie", new PieChartBuilder());
    this.register("scatter", new ScatterChartBuilder());
    this.register("line", new LineChartBuilder());
    this.register("forecast", new ForecastChartBuilder());
    this.register("anomaly", new AnomalyChartBuilder());
    this.register("segment", new SegmentChartBuilder());
    this.register("drivers", new DriversChartBuilder());
    this.register("bar", new BarChartBuilder());
  }

  register(chartType, builder) {
    this.builders.set(chartType, builder);
  }

  get(chartType) {
    return this.builders.get(chartType);
  }

  render(res, ctx) {
    const builder = this.get(res.chart_type);
    if (!builder) {
      console.warn(`Unknown chart type: ${res.chart_type}, falling back to bar`);
      return this.get("bar").build(res, ctx);
    }
    return builder.build(res, ctx);
  }
}

export const chartRegistry = new ChartRegistry();
