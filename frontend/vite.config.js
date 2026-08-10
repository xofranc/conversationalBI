import { defineConfig } from 'vite';
import { fileURLToPath } from 'node:url';

export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        // La home es la puerta de entrada; la consola y roadmap viven en pages/
        main: fileURLToPath(new URL('./index.html', import.meta.url)),
        app: fileURLToPath(new URL('./pages/app.html', import.meta.url)),
        roadmap: fileURLToPath(new URL('./pages/roadmap.html', import.meta.url)),
      },
    },
  },
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
