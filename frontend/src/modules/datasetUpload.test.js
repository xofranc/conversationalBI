import { describe, it, expect, vi, beforeEach } from 'vitest';
import { setupUpload, handleUpload } from './datasetUpload.js';
import { api } from '../lib/api.js';
import { eventBus } from '../lib/eventBus.js';

// Mock dependencies
vi.mock('../lib/api.js', () => ({
  api: {
    dataset: {
      upload: vi.fn(),
    },
  },
}));

vi.mock('../utils/ui.js', () => ({
  showToast: vi.fn(),
}));

vi.mock('../animations.js', () => ({
  animations: {
    showLoader: vi.fn(),
    hideLoader: vi.fn(),
  },
}));

beforeEach(() => {
  vi.clearAllMocks();
  
  // Mock DOM elements
  global.document = {
    getElementById: vi.fn((id) => ({
      addEventListener: vi.fn(),
      click: vi.fn(),
      value: '',
    })),
  };
});

describe('setupUpload', () => {
  it('should setup event listeners on drop zone', () => {
    setupUpload();
    expect(global.document.getElementById).toHaveBeenCalledWith('drop-zone');
    expect(global.document.getElementById).toHaveBeenCalledWith('file-upload');
  });
});

describe('handleUpload', () => {
  it('should reject invalid file extensions', async () => {
    const file = { name: 'test.pdf' };
    await handleUpload(file);
    // Should show error toast
  });

  it('should accept CSV files', async () => {
    const file = { name: 'test.csv' };
    api.dataset.upload.mockResolvedValue({ id: 1 });
    
    await handleUpload(file);
    
    expect(api.dataset.upload).toHaveBeenCalled();
  });

  it('should accept Excel files', async () => {
    const file = { name: 'test.xlsx' };
    api.dataset.upload.mockResolvedValue({ id: 1 });
    
    await handleUpload(file);
    
    expect(api.dataset.upload).toHaveBeenCalled();
  });

  it('should accept JSON files', async () => {
    const file = { name: 'test.json' };
    api.dataset.upload.mockResolvedValue({ id: 1 });
    
    await handleUpload(file);
    
    expect(api.dataset.upload).toHaveBeenCalled();
  });

  it('should handle upload errors', async () => {
    const file = { name: 'test.csv' };
    api.dataset.upload.mockRejectedValue({ data: 'Error' });
    
    await handleUpload(file);
    // Should show error toast
  });
});
