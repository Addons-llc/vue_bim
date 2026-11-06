import { onBeforeUnmount, watchEffect } from 'vue'
import { APP_BASE } from '../router/base'

// Keep these in step with buy_in_minutes/seo.py, which renders the same tags on the
// server for the first page load. These keep them right as shoppers move around the app.
export const SITE_NAME = 'Buy In Minutes'
export const DEFAULT_TITLE = 'BUY IN MINUTES'
export const DEFAULT_DESCRIPTION =
  'Order groceries, fresh produce and everyday essentials from local stores and get them delivered in minutes.'
const DEFAULT_IMAGE = '/assets/buy_in_minutes/buy-in-minutes/bim.jpeg'
const DESCRIPTION_LIMIT = 160

function absoluteUrl(url = '') {
  try {
    return new URL(url || DEFAULT_IMAGE, window.location.origin).href
  } catch {
    return ''
  }
}

function cleanDescription(text = '') {
  const plain = new DOMParser()
    .parseFromString(String(text || ''), 'text/html')
    .body.textContent.replace(/\s+/g, ' ')
    .trim()

  if (plain.length <= DESCRIPTION_LIMIT) {
    return plain
  }

  return `${plain.slice(0, DESCRIPTION_LIMIT - 1).replace(/\s+\S*$/, '')}…`
}

function setMeta(attribute, key, content) {
  let element = document.head.querySelector(`meta[${attribute}="${key}"]`)

  if (content === null) {
    element?.remove()
    return
  }

  if (!element) {
    element = document.createElement('meta')
    element.setAttribute(attribute, key)
    document.head.appendChild(element)
  }

  element.setAttribute('content', content)
}

function setCanonical(href) {
  let element = document.head.querySelector('link[rel="canonical"]')

  if (href === null) {
    element?.remove()
    return
  }

  if (!element) {
    element = document.createElement('link')
    element.setAttribute('rel', 'canonical')
    document.head.appendChild(element)
  }

  element.setAttribute('href', href)
}

/** Format a page title the same way the server does: "Name | Buy In Minutes". */
export function pageTitle(name, suffix = '') {
  const label = String(name || '').trim()
  return label ? `${label}${suffix} | ${SITE_NAME}` : DEFAULT_TITLE
}

/**
 * Apply title, description, canonical, robots and Open Graph tags.
 * `path` is the in-app route.path (already encoded); query strings stay out of the canonical.
 */
export function applyPageMeta({ title, description, image, path = '/', noindex = false } = {}) {
  const resolvedTitle = title || DEFAULT_TITLE
  const resolvedDescription = cleanDescription(description) || DEFAULT_DESCRIPTION
  // route.path is already percent-encoded by vue-router.
  const canonical = absoluteUrl(`${APP_BASE.replace(/\/$/, '')}${path || '/'}`)
  const imageUrl = absoluteUrl(image)

  document.title = resolvedTitle
  setMeta('name', 'description', resolvedDescription)
  setMeta('name', 'robots', noindex ? 'noindex, follow' : null)
  setCanonical(noindex ? null : canonical)
  setMeta('property', 'og:title', resolvedTitle)
  setMeta('property', 'og:description', resolvedDescription)
  setMeta('property', 'og:url', canonical)
  setMeta('property', 'og:image', imageUrl)
  setMeta('name', 'twitter:title', resolvedTitle)
  setMeta('name', 'twitter:description', resolvedDescription)
  setMeta('name', 'twitter:image', imageUrl)
}

/**
 * Reactive page meta for detail pages. `getMeta` runs inside a watchEffect, so tags update
 * once the record loads. Return null while loading to leave the current tags alone.
 */
export function usePageMeta(getMeta) {
  let active = true

  const stop = watchEffect(() => {
    const meta = getMeta()

    if (active && meta) {
      applyPageMeta(meta)
    }
  })

  onBeforeUnmount(() => {
    active = false
    stop()
  })
}
