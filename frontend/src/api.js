// API Service for ConversationalBI
// Base URL: en dev y en compose se usa el proxy same-origin (/api/v1).
// Sobreescribible con VITE_API_URL (p. ej. http://localhost:8000/api/v1).

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

export const api = {
  getToken() {
    return localStorage.getItem('access_token');
  },

  getRefreshToken() {
    return localStorage.getItem('refresh_token');
  },

  setTokens(access, refresh) {
    localStorage.setItem('access_token', access);
    if (refresh) localStorage.setItem('refresh_token', refresh);
  },

  clearTokens() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  async _fetch(endpoint, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // FormData: el navegador define el boundary multipart
    if (options.body instanceof FormData) {
      delete headers['Content-Type'];
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 204) return { response, data: null };
    const data = await response.json().catch(() => ({}));
    return { response, data };
  },

  async request(endpoint, options = {}, _retried = false) {
    const { response, data } = await this._fetch(endpoint, options);

    // Access token expirado → intentar un refresh y reintentar una vez
    if (response.status === 401 && !_retried && this.getRefreshToken()) {
      const refreshed = await this._refreshAccessToken();
      if (refreshed) return this.request(endpoint, options, true);
    }

    if (!response.ok) {
      throw { status: response.status, data };
    }

    return data;
  },

  async _refreshAccessToken() {
    try {
      const response = await fetch(`${API_BASE_URL}/users/token/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh: this.getRefreshToken() }),
      });
      if (!response.ok) {
        this.clearTokens();
        return false;
      }
      const data = await response.json();
      // Con ROTATE_REFRESH_TOKENS el backend rota también el refresh
      this.setTokens(data.access, data.refresh);
      return true;
    } catch {
      this.clearTokens();
      return false;
    }
  },

  auth: {
    login: (email, password) => api.request('/users/login/', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    }),
    register: (email, password, first_name, last_name) => api.request('/users/register/', {
      method: 'POST',
      body: JSON.stringify({ email, password, first_name, last_name })
    }),
    logout: () => api.request('/users/logout/', {
      method: 'POST',
      body: JSON.stringify({ refresh: api.getRefreshToken() })
    }),
  },

  dataset: {
    upload: (file, name) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('name', name);
      return api.request('/dataset/', {
        method: 'POST',
        body: formData
      });
    },
    list: () => api.request('/dataset/'),
    delete: (id) => api.request(`/dataset/${id}/`, { method: 'DELETE' }),
  },

  query: {
    ask: (question, datasetId) => api.request('/queries/', {
      method: 'POST',
      body: JSON.stringify({ question, dataset_id: datasetId })
    }),
    history: (datasetId) => api.request(
      `/queries/${datasetId ? `?dataset_id=${datasetId}` : ''}`
    ),
    detail: (id) => api.request(`/queries/${id}/`)
  }
};
