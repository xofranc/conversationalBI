import { describe, it, expect, vi, beforeEach } from 'vitest';
import { DriversChartBuilder } from './DriversChartBuilder.js';

vi.mock('chart.js', () => ({
  Chart: vi.fn().mockImplementation(() => ({})),
}));

describe('DriversChartBuilder', () => {
  let builder;

  beforeEach(() => {
    builder = new DriversChartBuilder();
  });

  it('should build drivers chart', () => {
    const res = {
      chart_type: 'drivers',
      chart_config: { xKey: 'impacto', yKey: 'factor' },
      data: [
        { factor: 'Precio', impacto: 0.8 },
        { factor: 'Calidad', impacto: 0.6 },
      ],
    };
    const chart = builder.build(res, {});
    expect(chart).toBeDefined();
  });

  it('should use horizontal bar (indexAxis y)', () => {
    const res = {
      chart_type: 'drivers',
      chart_config: { xKey: 'impacto', yKey: 'factor' },
      data: [{ factor: 'Precio', impacto: 0.8 }],
    };

    const config = builder.getConfig(res);
    expect(config.type).toBe('bar');
    expect(config.options.indexAxis).toBe('y');
  });

  it('should color positive values teal and negative orange', () => {
    const res = {
      chart_type: 'drivers',
      chart_config: { xKey: 'impacto', yKey: 'factor' },
      data: [
        { factor: 'Precio', impacto: 0.8 },
        { factor: 'Descuento', impacto: -0.3 },
      ],
    };

    const config = builder.getConfig(res);
    expect(config.data.datasets[0].backgroundColor[0]).toBe('#0E5E6F');
    expect(config.data.datasets[0].backgroundColor[1]).toBe('#C77B21');
  });
});
