import { describe, it, expect, vi, beforeEach } from 'vitest';
import { eventBus } from './eventBus.js';

describe('eventBus', () => {
  beforeEach(() => {
    eventBus.clear();
  });

  it('should call handler when event is emitted', () => {
    const handler = vi.fn();
    eventBus.on('TEST_EVENT', handler);
    eventBus.emit('TEST_EVENT', { data: 123 });
    expect(handler).toHaveBeenCalledWith({ data: 123 });
  });

  it('should unsubscribe correctly', () => {
    const handler = vi.fn();
    const unsub = eventBus.on('TEST_EVENT', handler);
    unsub();
    eventBus.emit('TEST_EVENT', {});
    expect(handler).not.toHaveBeenCalled();
  });

  it('should not affect other handlers when one unsubscribes', () => {
    const handler1 = vi.fn();
    const handler2 = vi.fn();
    const unsub1 = eventBus.on('TEST_EVENT', handler1);
    eventBus.on('TEST_EVENT', handler2);
    unsub1();
    eventBus.emit('TEST_EVENT', {});
    expect(handler1).not.toHaveBeenCalled();
    expect(handler2).toHaveBeenCalled();
  });

  it('should support multiple events', () => {
    const handler1 = vi.fn();
    const handler2 = vi.fn();
    eventBus.on('EVENT_A', handler1);
    eventBus.on('EVENT_B', handler2);
    eventBus.emit('EVENT_A', 'a');
    eventBus.emit('EVENT_B', 'b');
    expect(handler1).toHaveBeenCalledWith('a');
    expect(handler2).toHaveBeenCalledWith('b');
  });

  it('should clear all listeners', () => {
    const handler = vi.fn();
    eventBus.on('TEST_EVENT', handler);
    eventBus.clear();
    eventBus.emit('TEST_EVENT', {});
    expect(handler).not.toHaveBeenCalled();
  });

  it('should call multiple handlers for same event', () => {
    const handler1 = vi.fn();
    const handler2 = vi.fn();
    eventBus.on('TEST_EVENT', handler1);
    eventBus.on('TEST_EVENT', handler2);
    eventBus.emit('TEST_EVENT', 'data');
    expect(handler1).toHaveBeenCalledWith('data');
    expect(handler2).toHaveBeenCalledWith('data');
  });

  it('should not call handlers for different events', () => {
    const handler = vi.fn();
    eventBus.on('EVENT_A', handler);
    eventBus.emit('EVENT_B', {});
    expect(handler).not.toHaveBeenCalled();
  });

  it('should pass undefined data when no data provided', () => {
    const handler = vi.fn();
    eventBus.on('TEST_EVENT', handler);
    eventBus.emit('TEST_EVENT');
    expect(handler).toHaveBeenCalledWith(undefined);
  });
});
