// frontend/src/modules/session.js

const SESSION_KEY = 'demo_session_id';

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

export function isDemoMode() {
  return !localStorage.getItem('auth_token');
}
