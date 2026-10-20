import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ForecastChartBuilder } from './ForecastChartBuilder.js';

vi.mock('chart.js', () => ({
  Chart: vi.fn().mockImplementation(() => ({})),
}));

describe('ForecastChartBuilder', () => {
  let builder;

  beforeEach(() => {
    builder = new ForecastChartBuilder();
  });

  it('should build forecast chart', () => {
    const res = {
      chart_type: 'forecast',
      chart_config: { xKey: 'mes', yKey: 'ventas', splitKey: 'tipo' },
      data: [
        { mes: '2024-01', ventas: 100, tipo: 'real' },
        { mes: '2024-02', ventas: 120, tipo: 'real' },
        { mes: '2024-03', ventas: 130, tipo: 'forecast' },
      ],
    };
    const chart = builder.build(res, {});
    expect(chart).toBeDefined();
  });

  it('should split real and forecast data', () => {
    const res = {
      chart_type: 'forecast',
      chart_config: { xKey: 'mes', yKey: 'ventas', splitKey: 'tipo' },
      data: [
        { mes: '2024-01', ventas: 100, tipo: 'real' },
        { mes: '2024-02', ventas: 120, tipo: 'real' },
        { mes: '2024-03', ventas: 130, tipo: 'forecast' },
      ],
    };

    const config = builder.getConfig(res);
    expect(config.type).toBe('line');
    expect(config.data.datasets.length).toBe(4);
  });

  it('should have 4 datasets: inferior, superior, Real, Pronostico', () => {
    const res = {
      chart_type: 'forecast',
      chart_config: { xKey: 'mes', yKey: 'ventas', splitKey: 'tipo' },
      data: [
        { mes: '2024-01', ventas: 100, tipo: 'real' },
        { mes: '2024-02', ventas: 130, tipo: 'forecast' },
      ],
    };

    const config = builder.getConfig(res);
    expect(config.data.datasets[0].label).toBe('inferior');
    expect(config.data.datasets[1].label).toBe('superior');
    expect(config.data.datasets[2].label).toBe('Real');
    expect(config.data.datasets[3].label).toBe('Pronóstico');
  });
});
