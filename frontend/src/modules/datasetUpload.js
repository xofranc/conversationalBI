// frontend/src/modules/datasetUpload.js
import { api } from "../lib/api.js";
import { showToast } from "../utils/ui.js";
import { animations } from "../animations.js";
import { eventBus } from "../lib/eventBus.js";

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
    dropZone.classList.add("drag-over");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("drag-over");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("border-petrol-bright", "bg-rail-raise");
    if (e.dataTransfer.files.length) handleUpload(e.dataTransfer.files[0]);
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length) handleUpload(e.target.files[0]);
  });
}

export async function handleUpload(file) {
  const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
  if (![".csv", ".xlsx", ".json"].includes(ext)) {
    showToast("Solo se permiten archivos CSV, Excel o JSON.", "error");
    return;
  }

  try {
    animations.showLoader("Procesando dataset...");
    const name = file.name.replace(/\.[^.]+$/, "");
    const dataset = await api.dataset.upload(file, name);
    eventBus.emit('DATASET_UPLOADED', { dataset });
  } catch (err) {
    showToast(
      `Error al cargar el archivo. ${err?.data ? JSON.stringify(err.data) : ""}`.trim(),
      "error",
    );
  } finally {
    animations.hideLoader();
    document.getElementById("file-upload").value = "";
  }
}
