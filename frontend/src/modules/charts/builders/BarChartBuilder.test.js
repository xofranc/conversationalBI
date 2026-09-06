import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BarChartBuilder } from './BarChartBuilder.js';

vi.mock('chart.js', () => ({
  Chart: vi.fn().mockImplementation(() => ({})),
}));

describe('BarChartBuilder', () => {
  let builder;

  beforeEach(() => {
    builder = new BarChartBuilder();
  });

  it('should build bar chart', () => {
    const res = {
      chart_type: 'bar',
      chart_config: { xKey: 'ciudad', yKey: 'ventas' },
      data: [
        { ciudad: 'Bogota', ventas: 100 },
        { ciudad: 'Cali', ventas: 200 },
      ],
    };
    const chart = builder.build(res, {});
    expect(chart).toBeDefined();
  });

  it('should return correct data structure', () => {
    const res = {
      chart_type: 'bar',
      chart_config: { xKey: 'ciudad', yKey: 'ventas' },
      data: [
        { ciudad: 'Bogota', ventas: 100 },
        { ciudad: 'Cali', ventas: 200 },
      ],
    };

    const config = builder.getConfig(res);
    expect(config.type).toBe('bar');
    expect(config.data.labels).toEqual(['Bogota', 'Cali']);
    expect(config.data.datasets[0].data).toEqual([100, 200]);
  });
});
