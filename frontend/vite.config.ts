/// <reference types="vitest" />
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const backendPort = env.VITE_BACKEND_PORT || '8080'

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      proxy: {
        '/api': {
          target: `http://localhost:${backendPort}`,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '')
        },
        '/static': {
          target: `http://localhost:${backendPort}`,
          changeOrigin: true,
        }
      }
    },
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: './src/test/setup.ts',
      css: true,
      exclude: [
        'node_modules/**',
        'dist/**',
        'tests/e2e/**',  // Exclude Playwright E2E tests
        '**/*.spec.ts'   // Exclude Playwright test files
      ],
      coverage: {
        provider: 'v8',
        reporter: ['text', 'json', 'html'],
        exclude: [
          'node_modules/',
          'src/test/',
          '**/*.d.ts',
          'dist/',
          'tests/e2e/'
        ],
        thresholds: {
          global: {
            branches: 90,
            functions: 90,
            lines: 90,
            statements: 90
          }
        }
      }
    }
  }
})
