import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import {defineConfig} from 'vite';

export default defineConfig(() => {
  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      },
    },
    server: {
      hmr: process.env.DISABLE_HMR !== 'true',
      // The Python virtual environment contains thousands of ML-runtime files.
      // Watching it can exhaust the OS file-watcher limit and crash Vite.
      watch: process.env.DISABLE_HMR === 'true'
        ? null
        : { ignored: ['**/backend/**'] },
      // Keep browser requests same-origin in local development. This avoids
      // CORS failures while forwarding API and uploaded-media requests to
      // the FastAPI service.
      proxy: {
        '/api': {
          target: process.env.VITE_BACKEND_URL || 'http://localhost:8000',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },
  };
});
