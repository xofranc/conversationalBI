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
import { mountParticleNetwork } from "./particle-network.js";

gsap.registerPlugin(ScrollTrigger);

const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

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
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000); // 5s timeout
    
    const response = await fetch(STATUS_ENDPOINT, {
      signal: controller.signal
    });
    
    clearTimeout(timeout);
    
    if (!response.ok) throw new Error("Network response was not ok");
    return await response.json();
  } catch (err) {
    console.warn(
      "No se pudo cargar el estado del proyecto; usando datos locales.",
      err.message || err,
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

function setupScrollAnimations() {
  if (prefersReducedMotion) return;

  // Animar todos los elementos de reveal con ScrollTrigger batch
  const revealElements = gsap.utils.toArray("[data-landing-reveal]");
  if (revealElements.length > 0) {
    ScrollTrigger.batch(revealElements, {
      onEnter: (batch) => {
        gsap.to(batch, {
          y: 0,
          opacity: 1,
          duration: 0.7,
          stagger: 0.1,
          ease: "power3.out",
          overwrite: true,
        });
      },
      start: "top 85%",
    });
    // Estado inicial
    gsap.set(revealElements, { y: 30, opacity: 0 });
  }

  // Animar grupos de elementos
  const groupElements = gsap.utils.toArray("[data-landing-group]");
  groupElements.forEach((group) => {
    const children = gsap.utils.toArray(group.children);
    if (children.length > 0) {
      gsap.set(children, { y: 28, opacity: 0 });
      
      ScrollTrigger.create({
        trigger: group,
        start: "top 85%",
        once: true,
        onEnter: () => {
          gsap.to(children, {
            y: 0,
            opacity: 1,
            duration: 0.65,
            stagger: 0.12,
            ease: "power3.out",
          });
        },
      });
    }
  });

  // Animar módulos
  const moduleContainer = document.getElementById("modules-preview");
  if (moduleContainer) {
    const moduleCards = gsap.utils.toArray(moduleContainer.querySelectorAll('.module-card'));
    if (moduleCards.length > 0) {
      gsap.set(moduleCards, { y: 30, opacity: 0 });
      
      ScrollTrigger.create({
        trigger: moduleContainer,
        start: "top 85%",
        once: true,
        onEnter: () => {
          gsap.to(moduleCards, {
            y: 0,
            opacity: 1,
            duration: 0.6,
            stagger: 0.1,
            ease: "power3.out",
          });
        },
      });
    }
  }

  // Animar fases/roadmap
  const phasesContainer = document.getElementById("phases-preview");
  if (phasesContainer) {
    const phaseItems = gsap.utils.toArray(phasesContainer.querySelectorAll('.flex.items-center'));
    if (phaseItems.length > 0) {
      gsap.set(phaseItems, { x: -30, opacity: 0 });
      
      ScrollTrigger.create({
        trigger: phasesContainer,
        start: "top 85%",
        once: true,
        onEnter: () => {
          gsap.to(phaseItems, {
            x: 0,
            opacity: 1,
            duration: 0.5,
            stagger: 0.1,
            ease: "power3.out",
          });
        },
      });
    }
  }

  // Animar stack badges
  const stackSection = document.getElementById("stack");
  if (stackSection) {
    const stackBadges = gsap.utils.toArray(stackSection.querySelectorAll('.stack-badge'));
    if (stackBadges.length > 0) {
      gsap.set(stackBadges, { scale: 0.8, opacity: 0 });
      
      ScrollTrigger.create({
        trigger: stackSection,
        start: "top 85%",
        once: true,
        onEnter: () => {
          gsap.to(stackBadges, {
            scale: 1,
            opacity: 1,
            duration: 0.5,
            stagger: 0.05,
            ease: "back.out(1.4)",
          });
        },
      });
    }
  }

  // Animación de progreso
  const progressBar = document.getElementById("progress-preview-bar");
  if (progressBar) {
    const targetWidth = progressBar.style.width || '0%';
    progressBar.style.width = '0%';
    
    ScrollTrigger.create({
      trigger: progressBar,
      start: "top 90%",
      once: true,
      onEnter: () => {
        gsap.to(progressBar, {
          width: targetWidth,
          duration: 1.5,
          ease: "power3.out",
        });
      },
    });
  }
}

/* ── Orquestación ───────────────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", async () => {
  mountParticleNetwork();

  const chat = document.getElementById("demo-chat");
  const svg = document.getElementById("demo-svg");
  const sceneLabel = document.getElementById("demo-scene");

  // Animación de entrada del hero
  if (!prefersReducedMotion) {
    const intro = gsap.timeline({ defaults: { ease: "power3.out" } });
    intro
      .from(
        "[data-landing-line]",
        { y: 40, opacity: 0, duration: 0.9, stagger: 0.15 },
        0.1,
      )
      .from(
        "[data-landing]",
        { y: 25, opacity: 0, duration: 0.75, stagger: 0.1 },
        0.3,
      );
  }

  // Demo interactiva
  if (prefersReducedMotion) {
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

  // Marquee
  const track = document.getElementById("marquee-track");
  if (!prefersReducedMotion && track) {
    const drift = gsap.to(track, {
      xPercent: -50,
      ease: "none",
      duration: 28,
      repeat: -1,
    });
    
    const strip = track.closest(".marquee");
    if (strip) {
      strip.addEventListener("mouseenter", () => drift.pause());
      strip.addEventListener("mouseleave", () => drift.play());
    }
  }

  // Cargar datos del proyecto
  const data = await loadProjectData();
  console.log("Datos cargados:", data);
  
  const modules = data.modules || FALLBACK_DATA.modules;
  const phases = data.phases || FALLBACK_DATA.phases;
  
  console.log("Módulos:", modules.length);
  console.log("Fases:", phases.length);
  
  renderModules(modules);
  renderPhases(phases);
  updateProgressPreview(phases);

  // Configurar animaciones de scroll después de renderizar contenido dinámico
  setupScrollAnimations();
  
  // Refrescar ScrollTrigger
  if (!prefersReducedMotion) {
    ScrollTrigger.refresh();
  }
});
