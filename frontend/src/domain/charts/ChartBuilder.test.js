import { describe, it, expect } from 'vitest';
import { ChartBuilder } from './ChartBuilder.js';

describe('ChartBuilder', () => {
  it('should throw error when build() is called directly', () => {
    const builder = new ChartBuilder();
    expect(() => builder.build({}, {})).toThrow('subclass must implement build()');
  });

  it('should return base options with responsive true', () => {
    const builder = new ChartBuilder();
    const options = builder.getBaseOptions();
    expect(options.responsive).toBe(true);
    expect(options.maintainAspectRatio).toBe(false);
  });

  it('should have legend display false by default', () => {
    const builder = new ChartBuilder();
    const options = builder.getBaseOptions();
    expect(options.plugins.legend.display).toBe(false);
  });

  it('should return scale options', () => {
    const builder = new ChartBuilder();
    const scales = builder.getScaleOptions();
    expect(scales).toHaveProperty('x');
    expect(scales).toHaveProperty('y');
  });
});
