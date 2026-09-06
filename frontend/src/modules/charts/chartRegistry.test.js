import { describe, it, expect, vi, beforeEach } from 'vitest';
import { chartRegistry } from './ChartRegistry.js';

vi.mock('chart.js', () => ({
  Chart: vi.fn().mockImplementation(() => ({
    data: {},
    options: {},
  })),
}));

describe('ChartRegistry', () => {
  it('should have all 8 builders registered', () => {
    expect(chartRegistry.builders.size).toBe(8);
  });

  it('should have pie builder', () => {
    expect(chartRegistry.get('pie')).toBeDefined();
  });

  it('should have scatter builder', () => {
    expect(chartRegistry.get('scatter')).toBeDefined();
  });

  it('should have line builder', () => {
    expect(chartRegistry.get('line')).toBeDefined();
  });

  it('should have forecast builder', () => {
    expect(chartRegistry.get('forecast')).toBeDefined();
  });

  it('should have anomaly builder', () => {
    expect(chartRegistry.get('anomaly')).toBeDefined();
  });

  it('should have segment builder', () => {
    expect(chartRegistry.get('segment')).toBeDefined();
  });

  it('should have drivers builder', () => {
    expect(chartRegistry.get('drivers')).toBeDefined();
  });

  it('should have bar builder', () => {
    expect(chartRegistry.get('bar')).toBeDefined();
  });

  it('should render pie chart', () => {
    const res = {
      chart_type: 'pie',
      chart_config: { nameKey: 'ciudad', valueKey: 'ventas' },
      data: [{ ciudad: 'Bogota', ventas: 100 }],
    };
    const chart = chartRegistry.render(res, {});
    expect(chart).toBeDefined();
  });

  it('should fallback to bar for unknown type', () => {
    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const res = {
      chart_type: 'unknown',
      chart_config: { xKey: 'a', yKey: 'b' },
      data: [{ a: 1, b: 2 }],
    };
    const chart = chartRegistry.render(res, {});
    expect(chart).toBeDefined();
    expect(consoleSpy).toHaveBeenCalledWith('Unknown chart type: unknown, falling back to bar');
    consoleSpy.mockRestore();
  });
});
