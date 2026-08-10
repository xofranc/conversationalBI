import { api } from "../lib/api.js";
import { state } from "./state.js";
import { showToast } from "../utils/ui.js";
import { parseDrfError } from "../utils/format.js";

let callbacks = {};

export function initHistory(cbs) {
  callbacks = cbs;
}

export async function loadHistory() {
  if (!state.currentDatasetId) {
    renderHistory([]);
    return;
  }
  try {
    const data = await api.query.history(state.currentDatasetId);
    renderHistory(data.results || data || []);
  } catch {
    // La bitácora es secundaria: un fallo aquí no interrumpe la consola
  }
}

export function renderHistory(items) {
  const list = document.getElementById("history-list");
  const empty = document.getElementById("history-empty");
  if (!list) return;

  list.innerHTML = "";
  empty.classList.toggle("hidden", items.length > 0);

  items.forEach((q) => {
    const li = document.createElement("li");
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "history-item";
    btn.title = q.question;

    const time = new Date(q.created_at).toLocaleTimeString("es-CO", {
      hour: "2-digit",
      minute: "2-digit",
    });
    const status = !q.success ? "fail" : q.cached ? "cache" : "ok";

    const timeEl = document.createElement("span");
    timeEl.className = "h-time";
    timeEl.innerText = time;
    const qEl = document.createElement("span");
    qEl.className = "h-q";
    qEl.innerText = q.question;
    const statusEl = document.createElement("span");
    statusEl.className = `h-status ${status}`;

    btn.append(timeEl, qEl, statusEl);
    btn.addEventListener("click", () => openHistoryQuery(q.id));
    li.appendChild(btn);
    list.appendChild(li);
  });
}

export async function openHistoryQuery(id) {
  try {
    const q = await api.query.detail(id);
    if (!q.success || !q.result) {
      showToast("Esa consulta no tiene resultado guardado.", "error");
      return;
    }
    if (callbacks.onRestore) {
      callbacks.onRestore(q);
    }
    showToast("Consulta restaurada de la bitácora.", "success");
  } catch (err) {
    showToast(
      `No se pudo abrir la consulta. ${parseDrfError(err) || ""}`.trim(),
      "error",
    );
  }
}
