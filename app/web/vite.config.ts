/// <reference types="vitest/config" />
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
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
