// Cliente HTTP para el backend de ConversationalBI.
// En dev y en compose se usa el proxy same-origin (/api/v1).
// Sobreescribible con VITE_API_URL (p. ej. http://localhost:8000/api/v1).

import { supabase } from "./supabase.js";
import { API_BASE_URL } from "../config/constants.js";

export const api = {
  async getToken() {
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token;
  },

  async _fetch(endpoint, options = {}) {
    const headers = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    const token = await this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    // FormData: el navegador define el boundary multipart
    if (options.body instanceof FormData) {
      delete headers["Content-Type"];
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 204) return { response, data: null };
    const data = await response.json().catch(() => ({}));
    return { response, data };
  },

  async request(endpoint, options = {}) {
    const { response, data } = await this._fetch(endpoint, options);

    if (!response.ok) {
      throw { status: response.status, data };
    }

    return data;
  },

  auth: {
    register: (email, password, firstName, lastName) =>
      supabase.auth.signUp({
        email,
        password,
        options: {
          data: { first_name: firstName, last_name: lastName },
        },
      }),

    login: (email, password) =>
      supabase.auth.signInWithPassword({ email, password }),

    logout: () => supabase.auth.signOut(),
  },

  dataset: {
    upload: (file, name) => {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("name", name);
      return api.request("/dataset/", {
        method: "POST",
        body: formData,
      });
    },
    list: () => api.request("/dataset/"),
    delete: (id) => api.request(`/dataset/${id}/`, { method: "DELETE" }),
  },

  query: {
    ask: (question, datasetId) =>
      api.request("/queries/", {
        method: "POST",
        body: JSON.stringify({ question, dataset_id: datasetId }),
      }),
    history: (datasetId) =>
      api.request(`/queries/${datasetId ? `?dataset_id=${datasetId}` : ""}`),
    detail: (id) => api.request(`/queries/${id}/`),
  },
};
