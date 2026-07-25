import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    // En dev, /api se proxea al backend local (mismo puerto que CORS_ALLOWED_ORIGINS)
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
