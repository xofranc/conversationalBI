import {
  Chart,
  BarController,
  BarElement,
  LineController,
  LineElement,
  PieController,
  ArcElement,
  ScatterController,
  PointElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";

export function setupChartDefaults() {
  Chart.register(
    BarController,
    BarElement,
    LineController,
    LineElement,
    PieController,
    ArcElement,
    ScatterController,
    PointElement,
    CategoryScale,
    LinearScale,
    Tooltip,
    Legend,
    Filler,
  );

  Chart.defaults.font.family = '"Inter", system-ui, sans-serif';
  Chart.defaults.color = "#5C6672";
}
