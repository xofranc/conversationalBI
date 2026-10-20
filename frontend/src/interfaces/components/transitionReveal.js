(function() {
  var params = new URLSearchParams(window.location.search);
  var fromTransition = params.get('transition');

  if (fromTransition) {
    window.history.replaceState({}, '', window.location.pathname);

    // Simple approach: use CSS animation
    var overlay = document.getElementById('cta-transition-overlay');
    if (overlay) {
      overlay.style.opacity = '1';
      overlay.style.clipPath = 'circle(150% at 50% 50%)';
      overlay.style.pointerEvents = 'all';
      overlay.style.transition = 'clip-path 0.5s ease-in-out, opacity 0.5s ease-in-out 0.3s';

      setTimeout(function() {
        overlay.style.clipPath = 'circle(0% at 50% 50%)';
        overlay.style.opacity = '0';
      }, 100);

      setTimeout(function() {
        overlay.style.pointerEvents = 'none';
        overlay.style.transition = '';
      }, 800);
    }
  }
})();
