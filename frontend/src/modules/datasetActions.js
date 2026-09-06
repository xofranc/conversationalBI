// frontend/src/modules/datasetActions.js
import { api } from "../lib/api.js";
import { state } from "./state.js";
import { showToast } from "../utils/ui.js";
import { eventBus } from "../lib/eventBus.js";
import { renderDatasetList, syncDatasetLabels } from "./datasetRenderer.js";

export function selectDataset(id) {
  if (id === state.currentDatasetId) return;
  state.currentDatasetId = id;
  renderDatasetList();
  syncDatasetLabels();
  eventBus.emit('DATASET_SELECTED', { dataset: state.datasets.find((d) => d.id === id) || null });
}

export async function removeDataset(id) {
  try {
    await api.dataset.delete(id);
  } catch {
    // Si ya no existe en el backend, igual se desvincula localmente
  }
  const wasActive = id === state.currentDatasetId;
  state.datasets = state.datasets.filter((d) => d.id !== id);
  if (wasActive) {
    state.currentDatasetId = null;
    const firstReady = state.datasets.find((d) => d.status === "ready");
    state.currentDatasetId = firstReady ? firstReady.id : null;
  }
  renderDatasetList();
  syncDatasetLabels();
  eventBus.emit('DATASET_REMOVED', { wasActive });
  showToast("Fuente de datos eliminada.", "success");
}

export async function loadLibrary(selectId = null) {
  try {
    const list = await api.dataset.list();
    state.datasets = Array.isArray(list) ? list : list.results || [];
  } catch {
    state.datasets = [];
  }

  if (selectId && state.datasets.some((d) => d.id === selectId)) {
    state.currentDatasetId = selectId;
  } else if (
    !state.currentDatasetId ||
    !state.datasets.some((d) => d.id === state.currentDatasetId)
  ) {
    const firstReady = state.datasets.find((d) => d.status === "ready");
    state.currentDatasetId = firstReady ? firstReady.id : null;
  }

  renderDatasetList();
  syncDatasetLabels();
}
