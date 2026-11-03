/// <reference types="vitest/config" />
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    setupFiles: ['./src/test/setup.ts'],
    environment: 'jsdom',
  },
  server: {
    proxy: {
      '/api': 'http://localhost:5080',
    },
  },
});
