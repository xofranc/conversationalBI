// frontend/src/modules/session.js

const SESSION_KEY = 'demo_session_id';
const DEMO_FLAG = 'conversationalbi_demo';

/**
 * Detecta si estamos en modo demo.
 * Criterios:
 *   1. URL tiene ?demo=true
 *   2. Flag explicito en localStorage (seteado al entrar al demo)
 *   3. No hay auth_token (nunca ha hecho login)
 */
export function isDemoMode() {
  // Check URL param (safe for test environments)
  try {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('demo') === 'true') return true;
  } catch {
    // window.location not available in tests
  }

  // Check explicit demo flag
  if (localStorage.getItem(DEMO_FLAG) === '1') return true;

  // Fallback: no auth token = demo
  return !localStorage.getItem('auth_token');
}

/**
 * Marca la sesion como demo explicitamente.
 */
export function enterDemoMode() {
  localStorage.setItem(DEMO_FLAG, '1');
}

/**
 * Limpia el flag de demo.
 */
export function exitDemoMode() {
  localStorage.removeItem(DEMO_FLAG);
}

export function getSessionId() {
  let sessionId = localStorage.getItem(SESSION_KEY);
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, sessionId);
  }
  return sessionId;
}

export function clearSession() {
  localStorage.removeItem(SESSION_KEY);
}
