import { cpSync, mkdirSync, rmSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = dirname(fileURLToPath(import.meta.url))
const frontendDir = dirname(scriptDir)
const appDir = dirname(frontendDir)
const builtIndex = join(appDir, 'buy_in_minutes/public/buy-in-minutes/index.html')
const pageDir = join(appDir, 'buy_in_minutes/www/buy-in-minutes')

rmSync(pageDir, { recursive: true, force: true })
mkdirSync(pageDir, { recursive: true })
cpSync(builtIndex, join(pageDir, 'index.html'))
