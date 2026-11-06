// The storefront is served by Frappe at /buy-in-minutes/ (see `website_route_rules`
// in hooks.py). The Vite dev server falls back to index.html for any path, so the
// same base works there too.
export const APP_BASE = '/buy-in-minutes/'

/** Absolute path to an in-app route, e.g. appUrl('/login') -> '/buy-in-minutes/login'. */
export function appUrl(path = '') {
  return APP_BASE + String(path).replace(/^\/+/, '')
}

/**
 * Links shared before the switch to history routing look like
 * /buy-in-minutes#/products/ITEM. Rewrite them to the clean path before the
 * router reads the URL, so they keep working.
 */
export function migrateLegacyHashUrl() {
  const { hash } = window.location

  if (!hash.startsWith('#/')) {
    return
  }

  window.history.replaceState(window.history.state, '', appUrl(hash.slice(2)))
}
