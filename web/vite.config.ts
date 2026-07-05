/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Dev server proxies API calls to the observatory server (uvicorn :8000).
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/tables': 'http://localhost:8000',
      '/recordings': 'http://localhost:8000',
    },
  },
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts', 'src/**/*.test.tsx'],
  },
})
