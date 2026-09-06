const listeners = new Map();

export const eventBus = {
  on(event, callback) {
    if (!listeners.has(event)) listeners.set(event, []);
    listeners.get(event).push(callback);
    return () => {
      const cbs = listeners.get(event) || [];
      listeners.set(event, cbs.filter(cb => cb !== callback));
    };
  },

  emit(event, data) {
    const cbs = listeners.get(event) || [];
    cbs.forEach(cb => cb(data));
  },

  off(event, callback) {
    const cbs = listeners.get(event) || [];
    listeners.set(event, cbs.filter(cb => cb !== callback));
  },

  clear() {
    listeners.clear();
  },
};
