import gsap from '../../shared/gsap.js';

/**
 * Animación de salida/entrada compartida por los CTA entre páginas.
 * El markup del overlay vive en `views/shared/ctaTransition.html`.
 */
export function initCtaTransition({ linkSelector, destination, transitionDestination }) {
  document.addEventListener('DOMContentLoaded', () => {
    const overlay = document.getElementById('cta-transition-overlay');
    const ctaButtons = document.querySelectorAll(linkSelector);
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    ctaButtons.forEach(btn => {
      btn.addEventListener('pointerdown', () => {
        gsap.to(btn, {
          scale: 0.95,
          duration: 0.1,
          ease: 'power2.out'
        });
      });

      btn.addEventListener('pointerup', () => {
        gsap.to(btn, {
          scale: 1,
          duration: 0.2,
          ease: 'back.out(2)'
        });
      });

      btn.addEventListener('pointerleave', () => {
        gsap.to(btn, {
          scale: 1,
          duration: 0.2,
          ease: 'power2.out'
        });
      });

      btn.addEventListener('click', (e) => {
        e.preventDefault();

        if (prefersReducedMotion) {
          window.location.href = destination;
          return;
        }

        const rect = btn.getBoundingClientRect();
        const originX = rect.left + rect.width / 2;
        const originY = rect.top + rect.height / 2;
        const loading = overlay.querySelector('.cta-loading');
        const logoLetters = overlay.querySelectorAll('.cta-preloader-logo span');
        const line = overlay.querySelector('.cta-preloader-line');

        // Set overlay origin and show
        overlay.style.transformOrigin = `${originX}px ${originY}px`;
        overlay.style.opacity = '1';
        overlay.style.clipPath = `circle(0% at ${originX}px ${originY}px)`;
        overlay.style.pointerEvents = 'all';

        // Create timeline for loading animation
        const tl = gsap.timeline();

        tl.to(overlay, {
          clipPath: `circle(150% at ${originX}px ${originY}px)`,
          duration: 0.5,
          ease: 'power3.out'
        })
        .to(loading, {
          opacity: 1,
          duration: 0.2
        }, 0.3)
        .to(logoLetters, {
          opacity: 1,
          y: 0,
          duration: 0.4,
          stagger: 0.03,
          ease: 'power3.out'
        }, 0.4)
        .to(line, {
          width: '60px',
          duration: 0.8,
          ease: 'power2.inOut'
        }, 0.6)
        .call(() => {
          window.location.href = transitionDestination;
        }, null, 1.2);
      });
    });
  });
}
