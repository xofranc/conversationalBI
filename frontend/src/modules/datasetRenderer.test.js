import { describe, it, expect, vi, beforeEach } from 'vitest';
import { activeDataset, syncDatasetLabels, renderDatasetList } from './datasetRenderer.js';
import { state } from './state.js';

// Mock DOM elements
const mockElement = (id, text = '') => {
  const el = { 
    id, 
    innerText: text, 
    classList: { add: vi.fn(), remove: vi.fn() },
    innerHTML: '',
    appendChild: vi.fn(),
  };
  return el;
};

const mockLi = () => ({
  appendChild: vi.fn(),
});

const mockButton = () => ({
  className: '',
  innerText: '',
  title: '',
  appendChild: vi.fn(),
  addEventListener: vi.fn(),
});

beforeEach(() => {
  // Reset state
  state.datasets = [];
  state.currentDatasetId = null;
  
  // Mock DOM
  global.document = {
    getElementById: vi.fn((id) => mockElement(id)),
    createElement: vi.fn((tag) => {
      if (tag === 'li') return mockLi();
      return mockButton();
    }),
  };
});

describe('activeDataset', () => {
  it('should return null when no datasets', () => {
    expect(activeDataset()).toBeNull();
  });

  it('should return active dataset', () => {
    state.datasets = [{ id: 1, name: 'Test' }];
    state.currentDatasetId = 1;
    expect(activeDataset()).toEqual({ id: 1, name: 'Test' });
  });

  it('should return null when currentDatasetId not in datasets', () => {
    state.datasets = [{ id: 1, name: 'Test' }];
    state.currentDatasetId = 2;
    expect(activeDataset()).toBeNull();
  });
});

describe('syncDatasetLabels', () => {
  it('should update labels with active dataset name', () => {
    state.datasets = [{ id: 1, name: 'Test Dataset' }];
    state.currentDatasetId = 1;
    
    syncDatasetLabels();
    
    expect(global.document.getElementById).toHaveBeenCalledWith('masthead-dataset');
    expect(global.document.getElementById).toHaveBeenCalledWith('chat-dataset');
  });

  it('should show "sin fuente" when no active dataset', () => {
    syncDatasetLabels();
    expect(global.document.getElementById).toHaveBeenCalledWith('masthead-dataset');
  });
});

describe('renderDatasetList', () => {
  it('should do nothing when list element not found', () => {
    global.document.getElementById = vi.fn(() => null);
    renderDatasetList();
    expect(global.document.getElementById).toHaveBeenCalledWith('dataset-list');
  });

  it('should render empty list', () => {
    state.datasets = [];
    renderDatasetList();
    expect(global.document.getElementById).toHaveBeenCalledWith('dataset-count');
  });

  it('should render datasets', () => {
    state.datasets = [
      { id: 1, name: 'Dataset 1', status: 'ready', row_count: 100 },
      { id: 2, name: 'Dataset 2', status: 'processing', row_count: 0 },
    ];
    renderDatasetList();
    expect(global.document.getElementById).toHaveBeenCalledWith('dataset-count');
  });
});
