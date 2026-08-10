import { state } from "./state.js";
import { api } from "../lib/api.js";
import { animations } from "../animations.js";
import { showToast } from "../utils/ui.js";
import { parseDrfError } from "../utils/format.js";

let callbacks = {};
let chatInput;
let sendBtn;

export function initChat(cbs) {
  callbacks = cbs;
  chatInput = document.getElementById("chat-input");
  sendBtn = document.getElementById("send-btn");

  sendBtn.addEventListener("click", sendMessage);
  chatInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
  });

  // Chips de ejemplo: la pantalla vacía invita a actuar
  document.querySelectorAll(".example-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      chatInput.value = chip.dataset.question;
      chatInput.focus();
    });
  });
}

export function clearChat() {
  const chatContainer = document.getElementById("chat-messages");
  if (chatContainer) chatContainer.innerHTML = "";
}

export async function sendMessage() {
  const text = chatInput.value.trim();
  if (text.length < 5) {
    showToast("La pregunta debe tener al menos 5 caracteres.", "error");
    return;
  }
  if (!state.currentDatasetId) {
    showToast("Por favor, sube o activa una fuente de datos primero.", "error");
    return;
  }
  if (state.sending) return;

  state.sending = true;
  sendBtn.disabled = true;
  addMessageToChat("User", text);
  chatInput.value = "";

  try {
    const res = await api.query.ask(text, state.currentDatasetId);

    if (res.success) {
      addMessageToChat(
        "AI",
        res.answer || `${res.row_count} fila(s) encontradas.`,
        {
          sql: res.sql,
          execution_time: res.execution_time,
          cached: res.cached,
          model_used: res.model_used,
        },
      );
      if (callbacks.onResult) callbacks.onResult(res, text);
      if (callbacks.onHistoryUpdate) callbacks.onHistoryUpdate();
    } else {
      addMessageToChat(
        "AI",
        `No pude responder esa pregunta: ${res.error_msg || "error desconocido"}.`,
        null,
        res.suggestions || [],
      );
      if (callbacks.onHistoryUpdate) callbacks.onHistoryUpdate();
    }
  } catch (err) {
    if (err.status === 401) {
      showToast("Tu sesión expiró. Inicia sesión de nuevo.", "error");
      if (callbacks.onSessionExpired) callbacks.onSessionExpired();
      return;
    }
    showToast(
      `Ocurrió un error al procesar la consulta. ${parseDrfError(err) || ""}`.trim(),
      "error",
    );
  } finally {
    state.sending = false;
    sendBtn.disabled = false;
    chatInput.focus();
  }
}

export function addMessageToChat(sender, text, receipt = null, suggestions = []) {
  const chatContainer = document.getElementById("chat-messages");
  const wrapper = document.createElement("div");
  wrapper.className = `message-wrapper w-full mb-4 ${sender === "User" ? "items-end" : "items-start"}`;

  const bubble = document.createElement("div");
  bubble.className = `chat-message ${sender === "User" ? "user" : "ai"}`;
  bubble.innerText = text;
  wrapper.appendChild(bubble);

  if (receipt?.sql) {
    const details = document.createElement("details");
    details.className = "sql-receipt";

    const summary = document.createElement("summary");
    const label = document.createElement("span");
    label.innerText = `recibo · ${receipt.execution_time}s`;
    summary.appendChild(label);

    if (receipt.cached) {
      const badge = document.createElement("span");
      badge.className = "sql-badge cache";
      badge.innerText = "caché";
      summary.appendChild(badge);
    } else if (receipt.model_used) {
      const badge = document.createElement("span");
      badge.className = "sql-badge model";
      badge.innerText = receipt.model_used;
      summary.appendChild(badge);
    }

    const pre = document.createElement("pre");
    pre.innerText = receipt.sql;

    details.appendChild(summary);
    details.appendChild(pre);
    wrapper.appendChild(details);
  }

  if (suggestions.length) {
    const hint = document.createElement("p");
    hint.className = "suggestion-hint";
    hint.innerText = "Prueba con:";
    wrapper.appendChild(hint);

    const chips = document.createElement("div");
    chips.className = "suggestion-chips";
    suggestions.forEach((s) => {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "example-chip";
      chip.innerText = s;
      chip.addEventListener("click", () => {
        chatInput.value = s;
        chatInput.focus();
      });
      chips.appendChild(chip);
    });
    wrapper.appendChild(chips);
  }

  chatContainer.appendChild(wrapper);
  chatContainer.scrollTop = chatContainer.scrollHeight;
  animations.addChatMessage(bubble);
}
