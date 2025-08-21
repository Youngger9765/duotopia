import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      '**/*.spec.ts',
      '**/*.spec.tsx',
      '**/e2e/**',
    ],
    coverage: {
      reporter: ['text', 'json', 'html'],
    },
    onConsoleLog(log) {
      // 忽略測試中的 console.error
      if (log.includes('Invalid credentials')) return false
    },
  },
})