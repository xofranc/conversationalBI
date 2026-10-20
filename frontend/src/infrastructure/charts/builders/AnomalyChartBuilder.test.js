import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AnomalyChartBuilder } from './AnomalyChartBuilder.js';

vi.mock('chart.js', () => ({
  Chart: vi.fn().mockImplementation(() => ({})),
}));

describe('AnomalyChartBuilder', () => {
  let builder;

  beforeEach(() => {
    builder = new AnomalyChartBuilder();
  });

  it('should build anomaly chart', () => {
    const res = {
      chart_type: 'anomaly',
      chart_config: { xKey: 'fecha', yKey: 'valor' },
      data: [
        { fecha: 1, valor: 100 },
        { fecha: 2, valor: 999 },
      ],
    };
    const chart = builder.build(res, {});
    expect(chart).toBeDefined();
  });

  it('should use orange color for anomalies', () => {
    const res = {
      chart_type: 'anomaly',
      chart_config: { xKey: 'fecha', yKey: 'valor' },
      data: [{ fecha: 1, valor: 100 }],
    };

    const config = builder.getConfig(res);
    expect(config.type).toBe('scatter');
    expect(config.data.datasets[0].backgroundColor).toBe('#C77B21');
  });
});
