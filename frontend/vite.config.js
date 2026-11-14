import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/auth': 'http://127.0.0.1:8000',
      '/profile': 'http://127.0.0.1:8000',
      '/goal': 'http://127.0.0.1:8000',
      '/assessment': 'http://127.0.0.1:8000',
      '/recommendations': 'http://127.0.0.1:8000',
      '/progress': 'http://127.0.0.1:8000',
      '/roles': 'http://127.0.0.1:8000',
      '/skills': 'http://127.0.0.1:8000',
      '/security-controls': 'http://127.0.0.1:8000',
    }
  }
});

