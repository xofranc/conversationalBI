import gsap from 'gsap';

export const animations = {
  // Show global loader
  showLoader(text = "Procesando...") {
    const loader = document.getElementById('global-loader');
    document.getElementById('loader-text').innerText = text;
    loader.classList.remove('hidden');
    gsap.to(loader, { opacity: 1, duration: 0.3 });
  },

  hideLoader() {
    const loader = document.getElementById('global-loader');
    gsap.to(loader, { 
      opacity: 0, 
      duration: 0.3, 
      onComplete: () => loader.classList.add('hidden') 
    });
  },

  // Transition from Auth to Dashboard
  loginSuccess() {
    const authView = document.getElementById('auth-view');
    const dashboardView = document.getElementById('dashboard-view');
    
    gsap.to('.auth-container', {
      y: -50,
      opacity: 0,
      duration: 0.5,
      ease: "power2.in",
      onComplete: () => {
        authView.classList.add('hidden');
        dashboardView.classList.remove('hidden');
        
        // Staggered reveal of dashboard elements
        const tl = gsap.timeline();
        tl.to(dashboardView, { opacity: 1, duration: 0.4 })
          .from('aside', { x: -50, opacity: 0, duration: 0.5, ease: "power3.out" }, "-=0.2")
          .from('main header', { y: -20, opacity: 0, duration: 0.4, ease: "power2.out" }, "-=0.3")
          .from('#empty-state', { scale: 0.9, opacity: 0, duration: 0.5, ease: "back.out(1.2)" }, "-=0.2");
      }
    });
  },

  // Transition from Dashboard to Auth
  logout() {
    const authView = document.getElementById('auth-view');
    const dashboardView = document.getElementById('dashboard-view');
    
    gsap.to(dashboardView, {
      opacity: 0,
      duration: 0.5,
      onComplete: () => {
        dashboardView.classList.add('hidden');
        authView.classList.remove('hidden');
        gsap.to('.auth-container', { y: 0, opacity: 1, duration: 0.5, ease: "power3.out" });
      }
    });
  },

  // Add chat message
  addChatMessage(element) {
    gsap.from(element, {
      y: 20,
      opacity: 0,
      scale: 0.95,
      duration: 0.4,
      ease: "back.out(1.5)"
    });
  },

  // Reveal chart container
  revealChart() {
    const emptyState = document.getElementById('empty-state');
    const dashboardContent = document.getElementById('dashboard-content');

    if (!emptyState.classList.contains('hidden')) {
      gsap.to(emptyState, {
        opacity: 0, scale: 0.9, duration: 0.3,
        onComplete: () => {
          emptyState.classList.add('hidden');
          dashboardContent.classList.remove('hidden');
          
          gsap.from(dashboardContent.children, {
            y: 30, opacity: 0, duration: 0.6, stagger: 0.15, ease: "power3.out"
          });
        }
      });
    } else {
      // Just pulse it if already visible
      gsap.fromTo(dashboardContent, { opacity: 0.8 }, { opacity: 1, duration: 0.4, ease: "power2.out" });
    }
  }
};
