import { api } from "../lib/api.js";
import { state } from "./state.js";
import { showToast } from "../utils/ui.js";
import { animations } from "../animations.js";

let callbacks = {};

export function initDatasetLibrary(cbs) {
  callbacks = cbs;
}

export function activeDataset() {
  return state.datasets.find((d) => d.id === state.currentDatasetId) || null;
}

export function syncDatasetLabels() {
  const ds = activeDataset();
  const label = ds ? ds.name : "sin fuente";
  const masthead = document.getElementById("masthead-dataset");
  const chatLabel = document.getElementById("chat-dataset");
  if (masthead) masthead.innerText = label;
  if (chatLabel) chatLabel.innerText = ds ? ds.name : "sin fuente activa";
}

export function renderDatasetList() {
  const list = document.getElementById("dataset-list");
  const countEl = document.getElementById("dataset-count");
  if (!list) return;

  countEl.innerText = String(state.datasets.length);
  list.innerHTML = "";

  state.datasets.forEach((ds) => {
    const li = document.createElement("li");
    const item = document.createElement("button");
    item.type = "button";
    item.className = `dataset-item${ds.id === state.currentDatasetId ? " active" : ""}`;

    const meta =
      ds.status === "ready"
        ? `${Number(ds.row_count).toLocaleString("es-CO")} filas`
        : ds.status;

    const dot = document.createElement("span");
    dot.className = "d-dot";
    const name = document.createElement("span");
    name.className = "d-name";
    name.innerText = ds.name;
    const metaEl = document.createElement("span");
    metaEl.className = "d-meta";
    metaEl.innerText = meta;
    const del = document.createElement("span");
    del.className = "d-delete";
    del.innerText = "×";
    del.title = `Eliminar ${ds.name}`;

    item.append(dot, name, metaEl, del);
    item.addEventListener("click", () => selectDataset(ds.id));
    del.addEventListener("click", (e) => {
      e.stopPropagation();
      removeDataset(ds.id);
    });

    li.appendChild(item);
    list.appendChild(li);
  });
}

export function selectDataset(id) {
  if (id === state.currentDatasetId) return;
  state.currentDatasetId = id;
  renderDatasetList();
  syncDatasetLabels();
  if (callbacks.onSelect) callbacks.onSelect(activeDataset());
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
  if (callbacks.onRemove) callbacks.onRemove(wasActive);
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
  if (callbacks.onLoad) callbacks.onLoad();
}

export function setupUpload() {
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-upload");

  dropZone.addEventListener("click", () => fileInput.click());
  dropZone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      fileInput.click();
    }
  });

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("border-petrol-bright", "bg-rail-raise");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("border-petrol-bright", "bg-rail-raise");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("border-petrol-bright", "bg-rail-raise");
    if (e.dataTransfer.files.length) handleUpload(e.dataTransfer.files[0]);
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length) handleUpload(e.target.files[0]);
  });

  async function handleUpload(file) {
    const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
    if (![".csv", ".xlsx", ".json"].includes(ext)) {
      showToast("Solo se permiten archivos CSV, Excel o JSON.", "error");
      return;
    }

    try {
      animations.showLoader("Procesando dataset...");
      const name = file.name.replace(/\.[^.]+$/, "");
      const dataset = await api.dataset.upload(file, name);
      if (callbacks.onUpload) callbacks.onUpload(dataset);
    } catch (err) {
      showToast(
        `Error al cargar el archivo. ${err?.data ? JSON.stringify(err.data) : ""}`.trim(),
        "error",
      );
    } finally {
      animations.hideLoader();
      fileInput.value = "";
    }
  }
}
