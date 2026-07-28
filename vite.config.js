import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const proxyTarget = env.VITE_PROXY_TARGET || 'http://localhost:8000'

  return {
    base: '/assets/buy_in_minutes/buy-in-minutes/',
    plugins: [vue()],
    build: {
      outDir: '../buy_in_minutes/public/buy-in-minutes',
      emptyOutDir: true,
    },
    server: {
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
          secure: true,
        },
        '/files': {
          target: proxyTarget,
          changeOrigin: true,
          secure: true,
        },
        '/private/files': {
          target: proxyTarget,
          changeOrigin: true,
          secure: true,
        },
      },
    },
  }
})
