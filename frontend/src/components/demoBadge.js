// frontend/src/components/demoBadge.js
import { isDemoMode } from "../modules/session.js";

export function initDemoBadge() {
  if (!isDemoMode()) return;
  
  const badge = document.createElement('div');
  badge.className = 'fixed top-4 right-4 z-50 bg-amber-500 text-white px-3 py-1 rounded-full text-xs font-mono';
  badge.textContent = 'MODO DEMO';
  badge.title = 'Los datos se eliminarán al cerrar la sesión';
  document.body.appendChild(badge);
}
