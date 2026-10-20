document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.nav-pill').forEach(pill => {
    pill.addEventListener('mousemove', (e) => {
      const rect = pill.getBoundingClientRect();
      pill.style.setProperty('--mouse-x', (e.clientX - rect.left) + 'px');
      pill.style.setProperty('--mouse-y', (e.clientY - rect.top) + 'px');
    });
  });
});
