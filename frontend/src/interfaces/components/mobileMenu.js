import gsap from '../../shared/gsap.js';

document.addEventListener('DOMContentLoaded', () => {
  const menuBtn = document.getElementById('mobile-menu-btn');
  const closeBtn = document.getElementById('mobile-menu-close');
  const fullscreenMenu = document.getElementById('mobile-menu-fullscreen');
  const iconMenu = document.getElementById('icon-menu');
  const iconClose = document.getElementById('icon-close');
  const navItems = fullscreenMenu?.querySelectorAll('.mobile-nav-item');
  const socialLinks = fullscreenMenu?.querySelector('.mobile-menu-social');

  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  let menuOpen = false;
  let menuTimeline = null;

  function openMenu() {
    if (menuOpen) return;
    menuOpen = true;

    // Kill existing animation
    if (menuTimeline) menuTimeline.kill();

    if (prefersReducedMotion) {
      fullscreenMenu.style.visibility = 'visible';
      fullscreenMenu.style.opacity = '1';
      iconMenu.classList.remove('visible');
      iconMenu.classList.add('hidden');
      iconClose.classList.remove('hidden');
      iconClose.classList.add('visible');
      menuBtn.setAttribute('aria-expanded', 'true');
      document.body.style.overflow = 'hidden';
      return;
    }

    // Set initial states with gsap.set
    gsap.set(navItems, { x: 30, opacity: 0 });
    gsap.set(socialLinks, { y: 20, opacity: 0 });

    // Create fluid timeline
    menuTimeline = gsap.timeline({
      onComplete: () => {
        menuBtn.setAttribute('aria-expanded', 'true');
      }
    });

    // Set initial state
    gsap.set(fullscreenMenu, {
      visibility: 'visible',
      clipPath: 'circle(0% at calc(100% - 48px) 48px)'
    });

    // Animate overlay with organic shape
    menuTimeline
      .to(fullscreenMenu, {
        opacity: 1,
        clipPath: 'circle(150% at calc(100% - 48px) 48px)',
        duration: 0.6,
        ease: 'power3.out'
      })
      .to(iconMenu, {
        rotation: 90,
        opacity: 0,
        duration: 0.2,
        ease: 'power2.in'
      }, 0)
      .to(iconClose, {
        rotation: 0,
        opacity: 1,
        duration: 0.2,
        ease: 'power2.out'
      }, 0.1)
      .to(navItems, {
        x: 0,
        opacity: 1,
        duration: 0.4,
        stagger: 0.06,
        ease: 'power3.out'
      }, 0.2)
      .to(socialLinks, {
        y: 0,
        opacity: 1,
        duration: 0.3,
        ease: 'power2.out'
      }, 0.4);

    document.body.style.overflow = 'hidden';
  }

  function closeMenu() {
    if (!menuOpen) return;
    menuOpen = false;

    if (prefersReducedMotion) {
      fullscreenMenu.style.visibility = 'hidden';
      fullscreenMenu.style.opacity = '0';
      iconMenu.classList.remove('hidden');
      iconMenu.classList.add('visible');
      iconClose.classList.remove('visible');
      iconClose.classList.add('hidden');
      menuBtn.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
      return;
    }

    // Kill existing animation
    if (menuTimeline) menuTimeline.kill();

    menuTimeline = gsap.timeline({
      onComplete: () => {
        fullscreenMenu.style.visibility = 'hidden';
        menuBtn.setAttribute('aria-expanded', 'false');
      }
    });

    menuTimeline
      .to(navItems, {
        x: -20,
        opacity: 0,
        duration: 0.2,
        stagger: 0.03,
        ease: 'power2.in'
      })
      .to(socialLinks, {
        y: 10,
        opacity: 0,
        duration: 0.2,
        ease: 'power2.in'
      }, 0)
      .to(iconClose, {
        rotation: -90,
        opacity: 0,
        duration: 0.2,
        ease: 'power2.in'
      }, 0)
      .to(iconMenu, {
        rotation: 0,
        opacity: 1,
        duration: 0.2,
        ease: 'power2.out'
      }, 0.1)
      .to(fullscreenMenu, {
        clipPath: 'circle(0% at calc(100% - 48px) 48px)',
        opacity: 0.8,
        duration: 0.4,
        ease: 'power2.inOut'
      }, 0.15);

    document.body.style.overflow = '';
  }

  menuBtn?.addEventListener('click', openMenu);
  closeBtn?.addEventListener('click', closeMenu);

  fullscreenMenu?.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', closeMenu);
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && menuOpen) {
      closeMenu();
    }
  });
});
