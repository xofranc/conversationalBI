import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ScatterChartBuilder } from './ScatterChartBuilder.js';

vi.mock('chart.js', () => ({
  Chart: vi.fn().mockImplementation(() => ({})),
}));

describe('ScatterChartBuilder', () => {
  let builder;

  beforeEach(() => {
    builder = new ScatterChartBuilder();
  });

  it('should build scatter chart', () => {
    const res = {
      chart_type: 'scatter',
      chart_config: { xKey: 'precio', yKey: 'cantidad' },
      data: [
        { precio: 10, cantidad: 5 },
        { precio: 20, cantidad: 8 },
      ],
    };
    const chart = builder.build(res, {});
    expect(chart).toBeDefined();
  });

  it('should return correct data structure', () => {
    const res = {
      chart_type: 'scatter',
      chart_config: { xKey: 'precio', yKey: 'cantidad' },
      data: [
        { precio: 10, cantidad: 5 },
        { precio: 20, cantidad: 8 },
      ],
    };

    const config = builder.getConfig(res);
    expect(config.type).toBe('scatter');
    expect(config.data.datasets[0].data).toEqual([
      { x: 10, y: 5 },
      { x: 20, y: 8 },
    ]);
  });
});
