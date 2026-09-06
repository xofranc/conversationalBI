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

  if (countEl) countEl.innerText = state.datasets.length ? `${state.datasets.length} fuentes` : '';
  list.innerHTML = "";

  state.datasets.forEach((ds) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = `dock-chip${ds.id === state.currentDatasetId ? " active" : ""}`;

    const name = document.createElement("span");
    name.innerText = ds.name;
    chip.appendChild(name);

    const remove = document.createElement("span");
    remove.className = "chip-remove";
    remove.innerText = "×";
    remove.title = `Eliminar ${ds.name}`;
    chip.appendChild(remove);

    chip.addEventListener("click", () => {
      import("./datasetActions.js").then((mod) => mod.selectDataset(ds.id));
    });
    remove.addEventListener("click", (e) => {
      e.stopPropagation();
      import("./datasetActions.js").then((mod) => mod.removeDataset(ds.id));
    });

    list.appendChild(chip);
  });
}
