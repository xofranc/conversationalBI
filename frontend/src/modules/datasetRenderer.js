// frontend/src/modules/datasetRenderer.js
import { state } from "./state.js";

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
    item.addEventListener("click", () => {
      // Will be connected by datasetActions
      import("./datasetActions.js").then((mod) => mod.selectDataset(ds.id));
    });
    del.addEventListener("click", (e) => {
      e.stopPropagation();
      import("./datasetActions.js").then((mod) => mod.removeDataset(ds.id));
    });

    li.appendChild(item);
    list.appendChild(li);
  });
}
