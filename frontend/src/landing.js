import "./styles/main.css";
import "./styles/landing.css";
import "./styles/console.css";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import {
  SCENES,
  sceneTimeline,
  renderStaticScene,
} from "./shared/demo.js";
import {
  FALLBACK_DATA,
  STATUS_ENDPOINT,
  MODULE_STATUS_CONFIG,
  PHASE_STATUS_CONFIG,
} from "./config/constants.js";

gsap.registerPlugin(ScrollTrigger);

const REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function renderModuleCard(mod) {
  const cfg = MODULE_STATUS_CONFIG[mod.status] || MODULE_STATUS_CONFIG.pending;
  return `
    <div class="module-card bg-paper border border-line rounded-xl p-6 transition-all duration-300 hover:-translate-y-2 hover:shadow-lift hover:border-petrol">
      <div class="flex items-start justify-between mb-4">
        <span class="text-2xl">${mod.icon || "◆"}</span>
        <span class="font-mono text-[0.58rem] tracking-wider uppercase px-2 py-1 rounded ${cfg.color}/10 ${cfg.text}">${cfg.label}</span>
      </div>
      <h3 class="font-display text-lg font-semibold text-ink mb-2">${mod.name}</h3>
      <p class="text-sm text-ink-soft leading-relaxed">${mod.description}</p>
    </div>
  `;
}

function renderPhasePreview(phase) {
  const cfg = PHASE_STATUS_CONFIG[phase.status] || PHASE_STATUS_CONFIG.pending;
  return `
    <div class="flex items-center gap-4 bg-card border border-line rounded-xl p-4 shadow-card hover:shadow-lift transition-all duration-300">
      <div class="w-10 h-10 rounded-full ${cfg.color} flex items-center justify-center text-white text-sm font-bold shrink-0">
        ${cfg.label.charAt(0)}
      </div>
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1">
          <h3 class="font-display text-base font-semibold text-ink truncate">${phase.name}</h3>
          <span class="font-mono text-[0.55rem] tracking-wider uppercase px-1.5 py-0.5 rounded ${cfg.color}/10 ${cfg.text}">${cfg.label}</span>
        </div>
        <p class="text-sm text-ink-soft truncate">${phase.description}</p>
      </div>
    </div>
  `;
}

function updateProgressPreview(phases) {
  const completed = phases.filter((p) => p.status === "completed").length;
  const inProgress = phases.filter((p) => p.status === "in_progress").length;
  const total = phases.length;
  const progress = Math.round(((completed + inProgress * 0.5) / total) * 100);

  const bar = document.getElementById("progress-preview-bar");
  const text = document.getElementById("progress-preview-text");
  if (bar) bar.style.width = `${progress}%`;
  if (text) text.textContent = `${progress}%`;
}

async function loadProjectData() {
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

function renderModules(modules) {
  const container = document.getElementById("modules-preview");
  if (!container) return;
  container.innerHTML = modules.slice(0, 6).map(renderModuleCard).join("");
}

function renderPhases(phases) {
  const container = document.getElementById("phases-preview");
  if (!container) return;
  container.innerHTML = phases.slice(0, 4).map(renderPhasePreview).join("");
}

/* ── Orquestación ───────────────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", async () => {
  const chat = document.getElementById("demo-chat");
  const svg = document.getElementById("demo-svg");
  const sceneLabel = document.getElementById("demo-scene");

  if (!REDUCED) {
    const intro = gsap.timeline({ defaults: { ease: "power3.out" } });
    intro
      .from(
        "[data-landing-line]",
        { y: 36, opacity: 0, duration: 0.85, stagger: 0.12 },
        0.1,
      )
      .from(
        "[data-landing]",
        { y: 22, opacity: 0, duration: 0.7, stagger: 0.09 },
        0.25,
      );
  }

  if (REDUCED) {
    if (chat && svg) renderStaticScene(SCENES[0], chat, svg, sceneLabel);
  } else if (chat && svg) {
    const master = gsap.timeline({ repeat: -1, delay: 1.1 });
    SCENES.forEach((scene) =>
      master.add(sceneTimeline(scene, chat, svg, sceneLabel)),
    );
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) master.pause();
      else master.play();
    });
  }

  const track = document.getElementById("marquee-track");
  if (!REDUCED && track) {
    const drift = gsap.to(track, {
      xPercent: -50,
      ease: "none",
      duration: 28,
      repeat: -1,
    });
    const strip = track.closest(".marquee");
    strip.addEventListener("mouseenter", () => drift.pause());
    strip.addEventListener("mouseleave", () => drift.play());
  }

  if (!REDUCED) {
    gsap.utils.toArray("[data-landing-reveal]").forEach((node) => {
      gsap.from(node, {
        y: 26,
        opacity: 0,
        duration: 0.7,
        ease: "power3.out",
        scrollTrigger: { trigger: node, start: "top 86%", once: true },
      });
    });

    gsap.utils.toArray("[data-landing-group]").forEach((group) => {
      gsap.from(group.children, {
        y: 24,
        opacity: 0,
        duration: 0.65,
        ease: "power3.out",
        stagger: 0.1,
        scrollTrigger: { trigger: group, start: "top 84%", once: true },
      });
    });
  }

  const data = await loadProjectData();
  renderModules(data.modules || FALLBACK_DATA.modules);
  renderPhases(data.phases || FALLBACK_DATA.phases);
  updateProgressPreview(data.phases || FALLBACK_DATA.phases);
});
