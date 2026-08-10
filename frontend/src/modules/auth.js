import { api } from "../lib/api.js";
import { supabase } from "../lib/supabase.js";
import { animations } from "../animations.js";
import { parseDrfError } from "../utils/format.js";

export async function checkSession() {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return !!session;
}

export function setupAuth({ onEnter, onLeave }) {
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");
  const authSubtitle = document.getElementById("auth-subtitle");
  const errorEl = document.getElementById("auth-error");

  // Toggle login/registro
  document.getElementById("show-register").addEventListener("click", (e) => {
    e.preventDefault();
    errorEl.classList.add("hidden");
    loginForm.classList.add("hidden");
    registerForm.classList.remove("hidden");
    authSubtitle.innerText = "Crea una cuenta para continuar";
  });

  document.getElementById("show-login").addEventListener("click", (e) => {
    e.preventDefault();
    errorEl.classList.add("hidden");
    registerForm.classList.add("hidden");
    loginForm.classList.remove("hidden");
    authSubtitle.innerText = "Inicia sesión para continuar";
  });

  // Login
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    try {
      errorEl.classList.add("hidden");
      animations.showLoader("Iniciando sesión...");
      const { error } = await api.auth.login(email, password);
      if (error) throw error;
      animations.hideLoader();
      enterDashboard(true, onEnter);
    } catch (err) {
      animations.hideLoader();
      errorEl.innerText =
        err.message ||
        err.data?.detail ||
        "Error al iniciar sesión. Verifica tus credenciales.";
      errorEl.classList.remove("hidden");
    }
  });

  // Registro
  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const firstName = document.getElementById("reg-first-name").value;
    const lastName = document.getElementById("reg-last-name").value;
    const email = document.getElementById("reg-email").value;
    const password = document.getElementById("reg-password").value;

    try {
      errorEl.classList.add("hidden");
      animations.showLoader("Creando cuenta...");
      const { error: signUpError } = await api.auth.register(
        email,
        password,
        firstName,
        lastName,
      );
      if (signUpError) throw signUpError;

      const { error: loginError } = await api.auth.login(email, password);
      if (loginError) throw loginError;

      animations.hideLoader();
      enterDashboard(true, onEnter);
    } catch (err) {
      animations.hideLoader();
      errorEl.innerText =
        err.message || parseDrfError(err) || "Error al crear la cuenta.";
      errorEl.classList.remove("hidden");
    }
  });

  // Logout
  document.getElementById("logout-btn").addEventListener("click", async () => {
    try {
      await api.auth.logout();
    } catch {
      // Si falla (red, token ya inválido), igual limpiamos la sesión local
    }
    onLeave();
  });

  // Escucha cambios de sesión desde otros tabs o el SDK
  supabase.auth.onAuthStateChange((event, session) => {
    if (event === "SIGNED_OUT" || !session) {
      onLeave();
    }
  });
}

export function enterDashboard(animate, onEnter) {
  if (animate) {
    animations.loginSuccess();
  } else {
    document.getElementById("auth-view").classList.add("hidden");
    const dashboard = document.getElementById("dashboard-view");
    dashboard.classList.remove("hidden");
    dashboard.style.opacity = "1";
  }
  if (onEnter) onEnter();
}
