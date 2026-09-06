import { describe, it, expect, vi, beforeEach } from 'vitest';
import { selectDataset, removeDataset, loadLibrary } from './datasetActions.js';
import { state } from './state.js';
import { api } from '../lib/api.js';
import { eventBus } from '../lib/eventBus.js';

// Mock dependencies
vi.mock('../lib/api.js', () => ({
  api: {
    dataset: {
      list: vi.fn(),
      delete: vi.fn(),
    },
  },
}));

vi.mock('../utils/ui.js', () => ({
  showToast: vi.fn(),
}));

vi.mock('./datasetRenderer.js', () => ({
  renderDatasetList: vi.fn(),
  syncDatasetLabels: vi.fn(),
}));

beforeEach(() => {
  state.datasets = [];
  state.currentDatasetId = null;
  vi.clearAllMocks();
});

describe('selectDataset', () => {
  it('should do nothing if same dataset selected', () => {
    state.currentDatasetId = 1;
    selectDataset(1);
    expect(state.currentDatasetId).toBe(1);
  });

  it('should select new dataset', () => {
    state.datasets = [{ id: 1, name: 'Test' }];
    selectDataset(1);
    expect(state.currentDatasetId).toBe(1);
  });
});

describe('removeDataset', () => {
  it('should remove dataset and emit event', async () => {
    state.datasets = [{ id: 1, name: 'Test' }];
    state.currentDatasetId = 1;
    
    await removeDataset(1);
    
    expect(api.dataset.delete).toHaveBeenCalledWith(1);
    expect(state.datasets).toEqual([]);
    expect(state.currentDatasetId).toBeNull();
  });

  it('should keep other datasets when removing one', async () => {
    state.datasets = [{ id: 1, name: 'Test 1' }, { id: 2, name: 'Test 2' }];
    state.currentDatasetId = 1;
    
    await removeDataset(1);
    
    expect(state.datasets).toEqual([{ id: 2, name: 'Test 2' }]);
  });
});

describe('loadLibrary', () => {
  it('should load datasets from API', async () => {
    api.dataset.list.mockResolvedValue([{ id: 1, name: 'Test', status: 'ready' }]);
    
    await loadLibrary();
    
    expect(state.datasets).toEqual([{ id: 1, name: 'Test', status: 'ready' }]);
    expect(state.currentDatasetId).toBe(1);
  });

  it('should handle API error', async () => {
    api.dataset.list.mockRejectedValue(new Error('API Error'));
    
    await loadLibrary();
    
    expect(state.datasets).toEqual([]);
    expect(state.currentDatasetId).toBeNull();
  });

  it('should select specific dataset if provided', async () => {
    api.dataset.list.mockResolvedValue([{ id: 1 }, { id: 2 }]);
    
    await loadLibrary(2);
    
    expect(state.currentDatasetId).toBe(2);
  });
});
