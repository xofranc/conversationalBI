import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

// Registrar plugins
gsap.registerPlugin(ScrollTrigger);

// Configuración global
gsap.config({
  force3D: true,
});

const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// Sistema de animación para scroll reveals
export const scrollAnimations = {
  // Revelar elementos individuales
  reveal(elements, options = {}) {
    if (prefersReducedMotion) return;
    
    const defaults = {
      y: 30,
      autoAlpha: 0,
      duration: 0.6,
      ease: "power3.out",
      stagger: 0.1,
    };
    
    const config = { ...defaults, ...options };
    
    gsap.from(elements, config);
  },

  // Revelar con batch para mejor rendimiento
  revealBatch(selector, options = {}) {
    if (prefersReducedMotion) return;
    
    const defaults = {
      y: 30,
      autoAlpha: 0,
      duration: 0.6,
      ease: "power3.out",
      stagger: 0.1,
      start: "top 85%",
      once: true,
    };
    
    const config = { ...defaults, ...options };
    
    ScrollTrigger.batch(selector, {
      onEnter: (elements) => {
        gsap.from(elements, {
          y: config.y,
          autoAlpha: config.autoAlpha,
          duration: config.duration,
          ease: config.ease,
          stagger: config.stagger,
        });
      },
      start: config.start,
      once: config.once,
    });
  },

  // Parallax sutil
  parallax(element, options = {}) {
    if (prefersReducedMotion) return;
    
    const defaults = {
      y: 50,
      ease: "none",
      start: "top bottom",
      end: "bottom top",
    };
    
    const config = { ...defaults, ...options };
    
    gsap.to(element, {
      y: config.y,
      ease: config.ease,
      scrollTrigger: {
        trigger: element,
        start: config.start,
        end: config.end,
        scrub: 1,
      },
    });
  },

  // Animación de progreso
  progress(element, options = {}) {
    if (prefersReducedMotion) return;
    
    const defaults = {
      width: "100%",
      duration: 1.5,
      ease: "power3.out",
    };
    
    const config = { ...defaults, ...options };
    
    gsap.to(element, {
      width: config.width,
      duration: config.duration,
      ease: config.ease,
    });
  }
};

// Sistema de animación para micro-interacciones
export const microInteractions = {
  // Hover effects
  hover(element, options = {}) {
    if (prefersReducedMotion) return;
    
    const defaults = {
      y: -3,
      scale: 1.02,
      duration: 0.2,
      ease: "power2.out",
    };
    
    const config = { ...defaults, ...options };
    
    element.addEventListener('mouseenter', () => {
      gsap.to(element, {
        y: config.y,
        scale: config.scale,
        duration: config.duration,
        ease: config.ease,
      });
    });
    
    element.addEventListener('mouseleave', () => {
      gsap.to(element, {
        y: 0,
        scale: 1,
        duration: config.duration,
        ease: config.ease,
      });
    });
  },

  // Press effects
  press(element, options = {}) {
    if (prefersReducedMotion) return;
    
    const defaults = {
      scale: 0.98,
      duration: 0.1,
      ease: "power2.in",
    };
    
    const config = { ...defaults, ...options };
    
    element.addEventListener('mousedown', () => {
      gsap.to(element, {
        scale: config.scale,
        duration: config.duration,
        ease: config.ease,
      });
    });
    
    element.addEventListener('mouseup', () => {
      gsap.to(element, {
        scale: 1,
        duration: config.duration,
        ease: "power2.out",
      });
    });
    
    element.addEventListener('mouseleave', () => {
      gsap.to(element, {
        scale: 1,
        duration: config.duration,
        ease: "power2.out",
      });
    });
  },

  // Focus effects
  focus(element, options = {}) {
    if (prefersReducedMotion) return;
    
    const defaults = {
      scale: 1.02,
      boxShadow: "0 0 0 3px rgba(14, 94, 111, 0.3)",
      duration: 0.2,
      ease: "power2.out",
    };
    
    const config = { ...defaults, ...options };
    
    element.addEventListener('focus', () => {
      gsap.to(element, {
        scale: config.scale,
        boxShadow: config.boxShadow,
        duration: config.duration,
        ease: config.ease,
      });
    });
    
    element.addEventListener('blur', () => {
      gsap.to(element, {
        scale: 1,
        boxShadow: "none",
        duration: config.duration,
        ease: "power2.out",
      });
    });
  }
};

// Sistema de animación para transiciones de página
export const pageTransitions = {
  // Fade in
  fadeIn(element, options = {}) {
    if (prefersReducedMotion) {
      element.style.opacity = '1';
      return;
    }
    
    const defaults = {
      autoAlpha: 0,
      duration: 0.5,
      ease: "power2.out",
    };
    
    const config = { ...defaults, ...options };
    
    gsap.fromTo(element,
      { autoAlpha: 0 },
      { autoAlpha: 1, duration: config.duration, ease: config.ease }
    );
  },

  // Fade out
  fadeOut(element, options = {}) {
    if (prefersReducedMotion) {
      element.style.opacity = '0';
      return;
    }
    
    const defaults = {
      autoAlpha: 1,
      duration: 0.5,
      ease: "power2.in",
    };
    
    const config = { ...defaults, ...options };
    
    gsap.to(element, {
      autoAlpha: 0,
      duration: config.duration,
      ease: config.ease,
    });
  },

  // Slide in
  slideIn(element, options = {}) {
    if (prefersReducedMotion) {
      element.style.opacity = '1';
      return;
    }
    
    const defaults = {
      y: 30,
      autoAlpha: 0,
      duration: 0.6,
      ease: "power3.out",
    };
    
    const config = { ...defaults, ...options };
    
    gsap.fromTo(element,
      { y: config.y, autoAlpha: 0 },
      { y: 0, autoAlpha: 1, duration: config.duration, ease: config.ease }
    );
  },

  // Slide out
  slideOut(element, options = {}) {
    if (prefersReducedMotion) {
      element.style.opacity = '0';
      return;
    }
    
    const defaults = {
      y: -30,
      autoAlpha: 1,
      duration: 0.6,
      ease: "power3.in",
    };
    
    const config = { ...defaults, ...options };
    
    gsap.to(element, {
      y: config.y,
      autoAlpha: 0,
      duration: config.duration,
      ease: config.ease,
    });
  },

  // Scale in
  scaleIn(element, options = {}) {
    if (prefersReducedMotion) {
      element.style.opacity = '1';
      return;
    }
    
    const defaults = {
      scale: 0.9,
      autoAlpha: 0,
      duration: 0.5,
      ease: "back.out(1.4)",
    };
    
    const config = { ...defaults, ...options };
    
    gsap.fromTo(element,
      { scale: config.scale, autoAlpha: 0 },
      { scale: 1, autoAlpha: 1, duration: config.duration, ease: config.ease }
    );
  },

  // Scale out
  scaleOut(element, options = {}) {
    if (prefersReducedMotion) {
      element.style.opacity = '0';
      return;
    }
    
    const defaults = {
      scale: 0.9,
      autoAlpha: 1,
      duration: 0.5,
      ease: "power2.in",
    };
    
    const config = { ...defaults, ...options };
    
    gsap.to(element, {
      scale: config.scale,
      autoAlpha: 0,
      duration: config.duration,
      ease: config.ease,
    });
  }
};

// Utility para cleanup de animaciones
export function cleanupAnimations() {
  ScrollTrigger.getAll().forEach(trigger => trigger.kill());
  gsap.killTweensOf("*");
}

// Utility para pausar/resumir animaciones
export function pauseAllAnimations() {
  gsap.globalTimeline.pause();
}

export function resumeAllAnimations() {
  gsap.globalTimeline.resume();
}

// Exportar gsap para uso directo
export { gsap };