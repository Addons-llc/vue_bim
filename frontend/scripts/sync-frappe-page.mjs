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

// Frappe renders this page through Jinja; index.py fills seo_head with per-URL tags.
const template = html.replace(defaultTitle, `{{ seo_head or "${defaultTitle}" }}`)

writeFileSync(join(pageDir, 'index.html'), template)
