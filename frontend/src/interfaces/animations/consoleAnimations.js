import gsap from "gsap";

// Helper optimizado para prefers-reduced-motion
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
const REDUCED = prefersReducedMotion.matches;

// Configuración global de GSAP para mejor rendimiento
gsap.config({
  force3D: true, // Forzar aceleración por hardware
});

// Helper para animar con will-change temporal
function animateWithWillChange(targets, vars) {
  if (REDUCED) {
    // Aplicar estado final inmediatamente
    if (vars.opacity !== undefined) gsap.set(targets, { opacity: vars.opacity });
    if (vars.y !== undefined) gsap.set(targets, { y: vars.y });
    if (vars.x !== undefined) gsap.set(targets, { x: vars.x });
    if (vars.scale !== undefined) gsap.set(targets, { scale: vars.scale });
    return;
  }

  // Añadir will-change dinámicamente
  const elements = gsap.utils.toArray(targets);
  elements.forEach(el => {
    if (el.style) el.style.willChange = 'transform, opacity';
  });

  // Animar con autoAlpha en lugar de opacity para mejor rendimiento
  const optimizedVars = { ...vars };
  if ('opacity' in optimizedVars) {
    optimizedVars.autoAlpha = optimizedVars.opacity;
    delete optimizedVars.opacity;
  }

  // Limpiar will-change después de la animación
  const originalOnComplete = optimizedVars.onComplete;
  optimizedVars.onComplete = function() {
    elements.forEach(el => {
      if (el.style) el.style.willChange = 'auto';
    });
    if (originalOnComplete) originalOnComplete.call(this);
  };

  return gsap.to(targets, optimizedVars);
}

// Moción deliberada y quieta: el informe no se agita, se asienta.
export const animations = {
  showLoader(text = "Procesando...") {
    const loader = document.getElementById("global-loader");
    document.getElementById("loader-text").innerText = text;
    loader.classList.remove("hidden");
    if (REDUCED) {
      loader.style.opacity = "1";
      return;
    }
    animateWithWillChange(loader, { autoAlpha: 1, duration: 0.25 });
  },

  hideLoader() {
    const loader = document.getElementById("global-loader");
    if (REDUCED) {
      loader.style.opacity = "0";
      loader.classList.add("hidden");
      return;
    }
    animateWithWillChange(loader, {
      autoAlpha: 0,
      duration: 0.25,
      onComplete: () => loader.classList.add("hidden"),
    });
  },

  // Transición auth → dashboard
  loginSuccess() {
    const authView = document.getElementById("auth-view");
    const dashboardView = document.getElementById("dashboard-view");

    if (REDUCED) {
      authView.classList.add("hidden");
      dashboardView.classList.remove("hidden");
      dashboardView.style.opacity = "1";
      return;
    }

    animateWithWillChange(".auth-container", {
      y: -24,
      autoAlpha: 0,
      duration: 0.4,
      ease: "power2.in",
      onComplete: () => {
        authView.classList.add("hidden");
        dashboardView.classList.remove("hidden");

        const tl = gsap.timeline();
        tl.to(dashboardView, { autoAlpha: 1, duration: 0.35 })
          .from(
            "aside",
            { x: -30, opacity: 0, duration: 0.45, ease: "power3.out" },
            "-=0.15",
          )
          .from(
            "main header",
            { y: -12, opacity: 0, duration: 0.35, ease: "power2.out" },
            "-=0.25",
          )
          .from(
            "#empty-state",
            { scale: 0.96, opacity: 0, duration: 0.4, ease: "back.out(1.2)" },
            "-=0.15",
          );
      },
    });
  },

  // Transición dashboard → auth
  logout() {
    const authView = document.getElementById("auth-view");
    const dashboardView = document.getElementById("dashboard-view");

    if (REDUCED) {
      dashboardView.classList.add("hidden");
      authView.classList.remove("hidden");
      const card = document.querySelector(".auth-container");
      card.style.opacity = "1";
      card.style.transform = "none";
      return;
    }

    animateWithWillChange(dashboardView, {
      autoAlpha: 0,
      duration: 0.4,
      onComplete: () => {
        dashboardView.classList.add("hidden");
        authView.classList.remove("hidden");
        animateWithWillChange(".auth-container", {
          y: 0,
          autoAlpha: 1,
          duration: 0.4,
          ease: "power3.out",
        });
      },
    });
  },

  // Mensaje de chat: aparece, sin rebote exagerado
  addChatMessage(element) {
    if (REDUCED) return;
    gsap.from(element, {
      y: 12,
      opacity: 0,
      duration: 0.3,
      ease: "power2.out",
    });
  },

  // El informe se revela como documento: una sola subida serena
  revealChart() {
    const emptyState = document.getElementById("empty-state");
    const dashboardContent = document.getElementById("dashboard-content");

    if (!emptyState.classList.contains("hidden")) {
      const show = () => {
        emptyState.classList.add("hidden");
        dashboardContent.classList.remove("hidden");
        if (!REDUCED) {
          gsap.from(dashboardContent.children, {
            y: 20,
            opacity: 0,
            duration: 0.5,
            stagger: 0.12,
            ease: "power3.out",
          });
        }
      };

      if (REDUCED) {
        show();
      } else {
        animateWithWillChange(emptyState, {
          opacity: 0,
          scale: 0.97,
          duration: 0.25,
          onComplete: show,
        });
      }
    } else if (!REDUCED) {
      gsap.fromTo(
        dashboardContent,
        { opacity: 0.85 },
        { opacity: 1, duration: 0.3, ease: "power2.out" },
      );
    }
  },

  // Nuevas funciones de utilidad
  // Animación para elementos que aparecen en scroll
  revealOnScroll(elements, options = {}) {
    if (REDUCED) return;
    
    const defaults = {
      y: 30,
      opacity: 0,
      duration: 0.6,
      ease: "power3.out",
      stagger: 0.1,
    };
    
    const config = { ...defaults, ...options };
    
    gsap.from(elements, config);
  },

  // Animación para elementos que desaparecen
  hideElement(element, options = {}) {
    if (REDUCED) {
      element.style.display = 'none';
      return;
    }
    
    const defaults = {
      autoAlpha: 0,
      duration: 0.3,
      ease: "power2.in",
    };
    
    const config = { ...defaults, ...options };
    
    gsap.to(element, {
      ...config,
      onComplete: () => {
        element.style.display = 'none';
        if (config.onComplete) config.onComplete();
      }
    });
  },

  // Animación para elementos que aparecen
  showElement(element, options = {}) {
    if (REDUCED) {
      element.style.display = '';
      element.style.opacity = '1';
      return;
    }
    
    const defaults = {
      opacity: 1,
      duration: 0.3,
      ease: "power2.out",
    };
    
    const config = { ...defaults, ...options };
    
    element.style.display = '';
    gsap.fromTo(element, 
      { opacity: 0 },
      config
    );
  },

  // Animación para hover de elementos interactivos
  animateHover(element, isEntering) {
    if (REDUCED) return;
    
    if (isEntering) {
      gsap.to(element, {
        y: -2,
        scale: 1.02,
        duration: 0.2,
        ease: "power2.out",
      });
    } else {
      gsap.to(element, {
        y: 0,
        scale: 1,
        duration: 0.2,
        ease: "power2.out",
      });
    }
  },

  // Animación para pulsaciones de botón
  animatePress(element, isPressed) {
    if (REDUCED) return;
    
    if (isPressed) {
      gsap.to(element, {
        scale: 0.98,
        duration: 0.1,
        ease: "power2.in",
      });
    } else {
      gsap.to(element, {
        scale: 1,
        duration: 0.1,
        ease: "power2.out",
      });
    }
  }
};
