import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = dirname(fileURLToPath(import.meta.url))
const frontendDir = dirname(scriptDir)
const appDir = dirname(frontendDir)
const builtIndex = join(appDir, 'buy_in_minutes/public/buy-in-minutes/index.html')
const pageDir = join(appDir, 'buy_in_minutes/www/buy-in-minutes')

// Only index.html is generated; index.py (the SEO context) lives next to it and must survive builds.
mkdirSync(pageDir, { recursive: true })

const defaultTitle = '<title>BUY IN MINUTES</title>'
const html = readFileSync(builtIndex, 'utf8')

if (!html.includes(defaultTitle)) {
  throw new Error(`sync-frappe-page: ${defaultTitle} not found in the built index.html`)
}

const appContainer = '<div id="app"></div>'

if (!html.includes(appContainer)) {
  throw new Error(`sync-frappe-page: ${appContainer} not found in the built index.html`)
}

// Shown only until Vue mounts (it replaces #app's contents), so crawlers that skip
// JavaScript still get the page text. Kept plain so the swap is not jarring.
const fallbackStyle = `<style>
      .bim-ssr-fallback { max-width: 960px; margin: 0 auto; padding: 24px 16px; font: 15px/1.5 system-ui, sans-serif; color: #111827; }
      .bim-ssr-fallback h1 { font-size: 22px; margin: 8px 0 12px; }
      .bim-ssr-fallback nav, .bim-ssr-fallback nav a { color: #6b7280; font-size: 13px; }
      .bim-ssr-fallback img { max-width: 100%; height: auto; border-radius: 12px; }
      .bim-ssr-fallback ul { padding-left: 18px; columns: 2; }
      .bim-ssr-fallback a { color: #00785f; }
    </style>`

// Frappe renders this page through Jinja; index.py fills seo_head / seo_body per URL.
const template = html
  .replace(defaultTitle, `{{ seo_head or "${defaultTitle}" }}\n    ${fallbackStyle}`)
  .replace(appContainer, '<div id="app">{{ seo_body or "" }}</div>')

writeFileSync(join(pageDir, 'index.html'), template)
