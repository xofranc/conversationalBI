import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SegmentChartBuilder } from './SegmentChartBuilder.js';

vi.mock('chart.js', () => ({
  Chart: vi.fn().mockImplementation(() => ({})),
}));

describe('SegmentChartBuilder', () => {
  let builder;

  beforeEach(() => {
    builder = new SegmentChartBuilder();
  });

  it('should build segment chart', () => {
    const res = {
      chart_type: 'segment',
      chart_config: { xKey: 'ingreso', yKey: 'gasto', segmentKey: 'region' },
      data: [
        { region: 'Norte', ingreso: 100, gasto: 80 },
        { region: 'Sur', ingreso: 150, gasto: 120 },
        { region: 'Norte', ingreso: 110, gasto: 85 },
      ],
    };
    const chart = builder.build(res, {});
    expect(chart).toBeDefined();
  });

  it('should group data by segment', () => {
    const res = {
      chart_type: 'segment',
      chart_config: { xKey: 'ingreso', yKey: 'gasto', segmentKey: 'region' },
      data: [
        { region: 'Norte', ingreso: 100, gasto: 80 },
        { region: 'Sur', ingreso: 150, gasto: 120 },
        { region: 'Norte', ingreso: 110, gasto: 85 },
      ],
    };

    const config = builder.getConfig(res);
    expect(config.type).toBe('scatter');
    expect(config.data.datasets.length).toBe(2);
  });
});
