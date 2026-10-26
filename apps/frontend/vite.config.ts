import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Same browser origin for /api, /admin, /ws, and Django session cookies.
// Set VITE_BACKEND_TARGET only to a Django server you control.
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
