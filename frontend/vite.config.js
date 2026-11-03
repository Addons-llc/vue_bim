import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { existsSync, readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const frontendRoot = dirname(fileURLToPath(import.meta.url))
const appRoot = resolve(frontendRoot, '..')
const localCertDir = resolve(frontendRoot, '.cert')
const localKeyPath = resolve(localCertDir, 'localhost-key.pem')
const localCertPath = resolve(localCertDir, 'localhost-cert.pem')

function getLocalHttpsConfig(env) {
  if (env.VITE_DEV_HTTPS !== '1') {
    return undefined
  }

  if (!existsSync(localKeyPath) || !existsSync(localCertPath)) {
    return undefined
  }

  return {
    key: readFileSync(localKeyPath),
    cert: readFileSync(localCertPath),
  }
}

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
  const https = command === 'serve' ? getLocalHttpsConfig(env) : undefined
  // The live site marks its session cookie `Secure`. Over plain-HTTP dev
  // (Safari on localhost, or any browser via a LAN IP) the browser silently
  // drops it, so every request after login runs as Guest. Strip the flag when
  // the dev server isn't HTTPS. Dev server only; production is untouched.
  const configureProxy = https
    ? undefined
    : (proxy) => {
        proxy.on('proxyRes', (proxyRes) => {
          const cookies = proxyRes.headers['set-cookie']

          if (Array.isArray(cookies)) {
            proxyRes.headers['set-cookie'] = cookies.map((cookie) => cookie.replace(/;\s*Secure/gi, ''))
          }
        })
      }
  const clientEnv = Object.fromEntries(
    Object.entries(env)
      .filter(([key]) => key.startsWith('VITE_'))
      .map(([key, value]) => [`import.meta.env.${key}`, JSON.stringify(value)]),
  )

  return {
    base,
    plugins: [vue()],
    define: clientEnv,
    resolve: {
      alias: {
        '@app-root': appRoot,
      },
    },
    build: {
      outDir: '../buy_in_minutes/public/buy-in-minutes',
      emptyOutDir: true,
    },
    server: {
      host: true,
      https,
      // Let phones reach the dev server through an ngrok tunnel.
      allowedHosts: ['.ngrok-free.app', '.ngrok-free.dev', '.ngrok.app'],
      fs: {
        allow: [appRoot],
      },
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
          secure: true,
          headers: frappeProxyHeaders,
          configure: configureProxy,
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
          configure: configureProxy,
        },
      },
    },
  }
})
