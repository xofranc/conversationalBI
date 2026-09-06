import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock localStorage
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: vi.fn((key) => store[key] || null),
    setItem: vi.fn((key, value) => { store[key] = value; }),
    removeItem: vi.fn((key) => { delete store[key]; }),
    clear: vi.fn(() => { store = {}; }),
  };
})();

// Apply mocks
global.localStorage = localStorageMock;

// Import after mocking
const { getSessionId, clearSession, isDemoMode } = await import('./session.js');

beforeEach(() => {
  localStorageMock.clear();
  vi.clearAllMocks();
});

describe('getSessionId', () => {
  it('should create new session if none exists', () => {
    localStorageMock.getItem.mockReturnValue(null);
    const id = getSessionId();
    expect(id).toBeDefined();
    expect(localStorageMock.setItem).toHaveBeenCalled();
  });

  it('should return same session on subsequent calls', () => {
    localStorageMock.getItem.mockReturnValue('existing-id');
    const id = getSessionId();
    expect(id).toBe('existing-id');
  });
});

describe('clearSession', () => {
  it('should remove session from localStorage', () => {
    clearSession();
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('demo_session_id');
  });
});

describe('isDemoMode', () => {
  it('should return true when no auth token', () => {
    localStorageMock.getItem.mockReturnValue(null);
    expect(isDemoMode()).toBe(true);
  });

  it('should return false when auth token exists', () => {
    localStorageMock.getItem.mockImplementation((key) => {
      if (key === 'auth_token') return 'test-token';
      return null;
    });
    expect(isDemoMode()).toBe(false);
  });
});
