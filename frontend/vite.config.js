import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const frontendRoot = dirname(fileURLToPath(import.meta.url))
const appRoot = resolve(frontendRoot, '..')

// https://vite.dev/config/
export default defineConfig(({ command, mode }) => {
  // Local-only overrides (frontend/.env.local) must never leak into a
  // production build — otherwise a dev-machine LAN IP or similar gets
  // baked into the bundle that ships to the live site. Only merge them
  // in when actually running the dev server.
  const env = {
    ...loadEnv(mode, appRoot, ''),
    ...(command === 'serve' ? loadEnv(mode, frontendRoot, '') : {}),
    ...process.env,
  }
  const proxyTarget = env.VITE_PROXY_TARGET || 'http://localhost:8000'
  const frappeApiAuthHeader =
    env.FRAPPE_API_KEY && env.FRAPPE_API_SECRET
      ? `token ${env.FRAPPE_API_KEY}:${env.FRAPPE_API_SECRET}`
      : ''
  const frappeProxyHeaders = frappeApiAuthHeader
    ? { Authorization: frappeApiAuthHeader }
    : undefined
  const base = command === 'serve' ? '/' : '/assets/buy_in_minutes/buy-in-minutes/'
  const clientEnv = Object.fromEntries(
    Object.entries(env)
      .filter(([key]) => key.startsWith('VITE_'))
      .map(([key, value]) => [`import.meta.env.${key}`, JSON.stringify(value)]),
  )

  return {
    base,
    plugins: [vue()],
    define: clientEnv,
    build: {
      outDir: '../buy_in_minutes/public/buy-in-minutes',
      emptyOutDir: true,
    },
    server: {
      host: true,
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
          secure: true,
          headers: frappeProxyHeaders,
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
          headers: frappeProxyHeaders,
        },
      },
    },
  }
})
