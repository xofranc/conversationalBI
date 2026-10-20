import { describe, it, expect, vi, beforeEach } from 'vitest';
import { LineChartBuilder } from './LineChartBuilder.js';

vi.mock('chart.js', () => ({
  Chart: vi.fn().mockImplementation(() => ({})),
}));

describe('LineChartBuilder', () => {
  let builder;

  beforeEach(() => {
    builder = new LineChartBuilder();
  });

  it('should build line chart', () => {
    const res = {
      chart_type: 'line',
      chart_config: { xKey: 'mes', yKey: 'total' },
      data: [
        { mes: '2024-01', total: 100 },
        { mes: '2024-02', total: 150 },
      ],
    };
    const chart = builder.build(res, {});
    expect(chart).toBeDefined();
  });

  it('should return correct data structure', () => {
    const res = {
      chart_type: 'line',
      chart_config: { xKey: 'mes', yKey: 'total' },
      data: [
        { mes: '2024-01', total: 100 },
        { mes: '2024-02', total: 150 },
      ],
    };

    const config = builder.getConfig(res);
    expect(config.type).toBe('line');
    expect(config.data.labels).toEqual(['2024-01', '2024-02']);
    expect(config.data.datasets[0].data).toEqual([100, 150]);
  });
});
