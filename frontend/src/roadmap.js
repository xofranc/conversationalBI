import "./styles/main.css";
import "./styles/landing.css";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import {
  FALLBACK_DATA,
  STATUS_ENDPOINT,
  STATUS_CONFIG,
  MODULE_STATUS_CONFIG,
} from "./config/constants.js";
import { formatDate } from "./utils/format.js";

gsap.registerPlugin(ScrollTrigger);

const REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function renderTimeline(phases) {
  const container = document.getElementById("timeline");

  phases.forEach((phase, index) => {
    const cfg = STATUS_CONFIG[phase.status] || STATUS_CONFIG.pending;
    const isLeft = index % 2 === 0;
    const dateLabel = formatDate(phase.date_completed);

    const item = document.createElement("div");
    item.className = `timeline-item relative flex items-center justify-between lg:justify-normal gap-8 mb-12 ${isLeft ? "lg:flex-row-reverse" : ""}`;
    item.innerHTML = `
      <div class="hidden lg:block w-5/12"></div>
      <div class="timeline-node z-10 w-10 h-10 rounded-full ${cfg.color} flex items-center justify-center text-white text-sm font-bold shadow-lift shrink-0">
        ${cfg.icon}
      </div>
      <div class="timeline-card w-full lg:w-5/12 bg-card border border-line rounded-xl p-6 shadow-card">
        <div class="flex items-center gap-3 mb-3">
          <span class="font-mono text-[0.6rem] tracking-[0.2em] uppercase ${cfg.text}">${cfg.label}</span>
          ${dateLabel ? `<span class="ml-auto font-mono text-[0.6rem] text-ink-soft">${dateLabel}</span>` : ""}
        </div>
        <h3 class="font-display text-xl font-semibold text-ink mb-2">${phase.name}</h3>
        <p class="text-sm text-ink-soft leading-relaxed">${phase.description}</p>
      </div>
    `;
    container.appendChild(item);
  });
}

function renderModules(modules) {
  const grid = document.getElementById("modules-grid");
  if (!grid) return;

  modules.forEach((mod) => {
    const cfg =
      MODULE_STATUS_CONFIG[mod.status] || MODULE_STATUS_CONFIG.pending;
    const card = document.createElement("div");
    card.className =
      "module-card bg-paper border border-line rounded-xl p-6 transition-all duration-300 hover:-translate-y-2 hover:shadow-lift hover:border-petrol";
    card.innerHTML = `
      <div class="flex items-start justify-between mb-4">
        <span class="text-2xl">${mod.icon || "◆"}</span>
        <span class="font-mono text-[0.58rem] tracking-wider uppercase px-2 py-1 rounded ${cfg.color}/10 ${cfg.text}">${cfg.label}</span>
      </div>
      <h3 class="font-display text-lg font-semibold text-ink mb-2">${mod.name}</h3>
      <p class="text-sm text-ink-soft leading-relaxed">${mod.description}</p>
    `;
    grid.appendChild(card);
  });
}

function updateProgress(phases) {
  const completed = phases.filter((p) => p.status === "completed").length;
  const inProgress = phases.filter((p) => p.status === "in_progress").length;
  const total = phases.length;
  const progress = Math.round(((completed + inProgress * 0.5) / total) * 100);

  document.getElementById("progress-bar").style.width = `${progress}%`;
  document.getElementById("progress-text").textContent = `${progress}%`;
}

function animate() {
  if (REDUCED) return;

  gsap.from("#progress-bar", {
    width: "0%",
    duration: 1.2,
    ease: "power2.out",
  });

  gsap.utils.toArray(".timeline-item").forEach((item, i) => {
    gsap.from(item, {
      y: 40,
      opacity: 0,
      duration: 0.7,
      ease: "power3.out",
      scrollTrigger: {
        trigger: item,
        start: "top 85%",
        once: true,
      },
      delay: i * 0.08,
    });
  });

  gsap.utils.toArray(".module-card").forEach((card, i) => {
    gsap.from(card, {
      y: 24,
      opacity: 0,
      duration: 0.6,
      ease: "power3.out",
      scrollTrigger: {
        trigger: card,
        start: "top 88%",
        once: true,
      },
      delay: i * 0.05,
    });
  });
}

async function loadData() {
  try {
    const response = await fetch(STATUS_ENDPOINT);
    if (!response.ok) throw new Error("Network response was not ok");
    return await response.json();
  } catch (err) {
    console.warn(
      "No se pudo cargar el estado del proyecto; usando datos locales.",
      err,
    );
    return FALLBACK_DATA;
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  const data = await loadData();
  renderTimeline(data.phases || FALLBACK_DATA.phases);
  renderModules(data.modules || FALLBACK_DATA.modules);
  updateProgress(data.phases || FALLBACK_DATA.phases);
  animate();
});
