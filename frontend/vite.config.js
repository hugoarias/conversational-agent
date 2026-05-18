import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.js'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov'],
      include: ['src/**/*.{js,jsx}'],
      exclude: [
        'src/main.jsx',          // app entry point
        'src/test/**',           // test setup
        '**/*.test.{js,jsx}',   // test files themselves
        'src/App.jsx',           // integration root; tested via components
        'src/hooks/useVAD.js',   // requires AudioWorklet + MediaDevices
      ],
    },
  },
});
