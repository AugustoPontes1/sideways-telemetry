import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Mesma origem no navegador: /api, /admin, /ws e cookies da sessão Django.
// Aponte VITE_BACKEND_TARGET apenas para um servidor Django sob seu controle.
const backend = process.env.VITE_BACKEND_TARGET || 'http://127.0.0.1:8000';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': { target: backend, changeOrigin: true },
      '/admin': { target: backend, changeOrigin: true },
      '/static': { target: backend, changeOrigin: true },
      '/healthz': { target: backend, changeOrigin: true },
      '/ws': { target: backend, changeOrigin: true, ws: true },
    },
  },
});
