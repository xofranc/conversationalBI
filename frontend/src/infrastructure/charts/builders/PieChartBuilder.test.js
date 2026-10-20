import { describe, it, expect, vi, beforeEach } from 'vitest';
import { PieChartBuilder } from './PieChartBuilder.js';

vi.mock('chart.js', () => ({
  Chart: vi.fn().mockImplementation(() => ({})),
}));

describe('PieChartBuilder', () => {
  let builder;

  beforeEach(() => {
    builder = new PieChartBuilder();
  });

  it('should be an instance of PieChartBuilder', () => {
    expect(builder).toBeInstanceOf(PieChartBuilder);
  });

  it('should build pie chart', () => {
    const res = {
      chart_type: 'pie',
      chart_config: { nameKey: 'ciudad', valueKey: 'ventas' },
      data: [
        { ciudad: 'Bogota', ventas: 100 },
        { ciudad: 'Cali', ventas: 200 },
      ],
    };
    const chart = builder.build(res, {});
    expect(chart).toBeDefined();
  });

  it('should return correct config structure', () => {
    const res = {
      chart_type: 'pie',
      chart_config: { nameKey: 'ciudad', valueKey: 'ventas' },
      data: [
        { ciudad: 'Bogota', ventas: 100 },
        { ciudad: 'Cali', ventas: 200 },
      ],
    };

    const config = builder.getConfig(res);
    expect(config.type).toBe('pie');
    expect(config.data.labels).toEqual(['Bogota', 'Cali']);
    expect(config.data.datasets[0].data).toEqual([100, 200]);
  });
});
