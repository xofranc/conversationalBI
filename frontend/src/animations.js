import gsap from 'gsap';

const REDUCED = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// Moción deliberada y quieta: el informe no se agita, se asienta.
export const animations = {
  showLoader(text = 'Procesando...') {
    const loader = document.getElementById('global-loader');
    document.getElementById('loader-text').innerText = text;
    loader.classList.remove('hidden');
    if (REDUCED) {
      loader.style.opacity = '1';
      return;
    }
    gsap.to(loader, { opacity: 1, duration: 0.25 });
  },

  hideLoader() {
    const loader = document.getElementById('global-loader');
    if (REDUCED) {
      loader.style.opacity = '0';
      loader.classList.add('hidden');
      return;
    }
    gsap.to(loader, {
      opacity: 0,
      duration: 0.25,
      onComplete: () => loader.classList.add('hidden'),
    });
  },

  // Transición auth → dashboard
  loginSuccess() {
    const authView = document.getElementById('auth-view');
    const dashboardView = document.getElementById('dashboard-view');

    if (REDUCED) {
      authView.classList.add('hidden');
      dashboardView.classList.remove('hidden');
      dashboardView.style.opacity = '1';
      return;
    }

    gsap.to('.auth-container', {
      y: -24,
      opacity: 0,
      duration: 0.4,
      ease: 'power2.in',
      onComplete: () => {
        authView.classList.add('hidden');
        dashboardView.classList.remove('hidden');

        const tl = gsap.timeline();
        tl.to(dashboardView, { opacity: 1, duration: 0.35 })
          .from('aside', { x: -30, opacity: 0, duration: 0.45, ease: 'power3.out' }, '-=0.15')
          .from('main header', { y: -12, opacity: 0, duration: 0.35, ease: 'power2.out' }, '-=0.25')
          .from('#empty-state', { scale: 0.96, opacity: 0, duration: 0.4, ease: 'back.out(1.2)' }, '-=0.15');
      },
    });
  },

  // Transición dashboard → auth
  logout() {
    const authView = document.getElementById('auth-view');
    const dashboardView = document.getElementById('dashboard-view');

    if (REDUCED) {
      dashboardView.classList.add('hidden');
      authView.classList.remove('hidden');
      const card = document.querySelector('.auth-container');
      card.style.opacity = '1';
      card.style.transform = 'none';
      return;
    }

    gsap.to(dashboardView, {
      opacity: 0,
      duration: 0.4,
      onComplete: () => {
        dashboardView.classList.add('hidden');
        authView.classList.remove('hidden');
        gsap.to('.auth-container', { y: 0, opacity: 1, duration: 0.4, ease: 'power3.out' });
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
      ease: 'power2.out',
    });
  },

  // El informe se revela como documento: una sola subida serena
  revealChart() {
    const emptyState = document.getElementById('empty-state');
    const dashboardContent = document.getElementById('dashboard-content');

    if (!emptyState.classList.contains('hidden')) {
      const show = () => {
        emptyState.classList.add('hidden');
        dashboardContent.classList.remove('hidden');
        if (!REDUCED) {
          gsap.from(dashboardContent.children, {
            y: 20,
            opacity: 0,
            duration: 0.5,
            stagger: 0.12,
            ease: 'power3.out',
          });
        }
      };

      if (REDUCED) {
        show();
      } else {
        gsap.to(emptyState, {
          opacity: 0,
          scale: 0.97,
          duration: 0.25,
          onComplete: show,
        });
      }
    } else if (!REDUCED) {
      gsap.fromTo(dashboardContent, { opacity: 0.85 }, { opacity: 1, duration: 0.3, ease: 'power2.out' });
    }
  },
};
