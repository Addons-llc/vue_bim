// Google Analytics 4 for the storefront.
//
// The gtag snippet is injected by the server (www/buy-in-minutes/index.py) only when
// `buy_in_minutes_ga_measurement_id` is set in site_config.json, so dev servers and sites
// without an ID load nothing and every call here is a no-op.
//
// Consent: analytics_storage starts "denied" (Consent Mode v2) until the visitor accepts
// in ConsentBanner. GA still receives cookieless pings before that, as Google intends.
// Never send personal data (email, phone, names): Google's terms forbid it.

const CONSENT_STORAGE_KEY = 'bim_analytics_consent'
const PURCHASE_STORAGE_KEY = 'bim_analytics_purchases'
const DEFAULT_CURRENCY = 'AED'

function gtag(...args) {
  if (typeof window.gtag === 'function') {
    window.gtag(...args)
  }
}

export function isAnalyticsEnabled() {
  return typeof window.gtag === 'function' && Boolean(window.BIM_GA_ID)
}

export function track(eventName, params = {}) {
  gtag('event', eventName, params)
}

// --- Consent ---------------------------------------------------------------

function readStorage(key) {
  try {
    return window.localStorage.getItem(key)
  } catch {
    return null
  }
}

function writeStorage(key, value) {
  try {
    window.localStorage.setItem(key, value)
  } catch {
    // Private mode / blocked storage: the choice just won't be remembered.
  }
}

/** 'granted' | 'denied' | null (not chosen yet). */
export function getConsentChoice() {
  const value = readStorage(CONSENT_STORAGE_KEY)
  return value === 'granted' || value === 'denied' ? value : null
}

export function setConsentChoice(choice) {
  writeStorage(CONSENT_STORAGE_KEY, choice)
  gtag('consent', 'update', { analytics_storage: choice === 'granted' ? 'granted' : 'denied' })
}

// --- Page views & users ------------------------------------------------------

export function trackPageView() {
  track('page_view', {
    page_location: window.location.href,
    page_path: window.location.pathname + window.location.search,
    page_title: document.title,
  })
}

async function sha256(text) {
  const bytes = new TextEncoder().encode(String(text))
  const digest = await window.crypto.subtle.digest('SHA-256', bytes)
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, '0')).join('')
}

/** Tie sessions to a signed-in shopper by a one-way hash of their user id (never the raw id). */
export async function setAnalyticsUser(userId) {
  if (!isAnalyticsEnabled()) {
    return
  }

  let hashed = null
  try {
    hashed = userId ? await sha256(`bim:${userId}`) : null
  } catch {
    hashed = null
  }

  gtag('config', window.BIM_GA_ID, { user_id: hashed, send_page_view: false })
}

// --- Ecommerce ---------------------------------------------------------------

function toNumber(value) {
  const number = Number(value)
  return Number.isFinite(number) ? number : 0
}

/** Map a storefront product / cart item / order row to a GA4 item. */
export function toAnalyticsItem(product = {}, extra = {}) {
  const item = {
    item_id: product.itemCode || product.item_code || product.id || '',
    item_name: product.name || product.item_name || product.itemCode || '',
    price: toNumber(product.price ?? product.rate ?? product.selling_price),
    quantity: toNumber(product.quantity ?? product.qty) || 1,
  }

  const brand = product.brand || product.item_brand
  const category = product.category || product.itemGroup || product.item_group
  const supplier = product.supplierName || product.supplier
  const variant = product.size || product.selectedSize

  if (brand) item.item_brand = brand
  if (category) item.item_category = category
  if (supplier) item.affiliation = supplier
  if (variant) item.item_variant = variant

  return { ...item, ...extra }
}

function itemsValue(items) {
  return items.reduce((total, item) => total + item.price * item.quantity, 0)
}

function currencyOf(products = []) {
  return products.find((product) => product?.currency)?.currency || DEFAULT_CURRENCY
}

function trackItems(eventName, products, params = {}) {
  if (!isAnalyticsEnabled()) {
    return
  }

  const list = (Array.isArray(products) ? products : [products]).filter(Boolean)
  const items = list.map((product, index) => toAnalyticsItem(product, { index }))

  if (!items.length) {
    return
  }

  track(eventName, {
    currency: currencyOf(list),
    value: Number(itemsValue(items).toFixed(2)),
    items,
    ...params,
  })
}

export function trackViewItem(product) {
  trackItems('view_item', product)
}

export function trackViewItemList(products, listName) {
  // GA caps items per event; the first page of a listing is what matters.
  trackItems('view_item_list', (products || []).slice(0, 30), {
    item_list_id: String(listName || '').toLowerCase().replace(/\s+/g, '_'),
    item_list_name: listName || '',
  })
}

export function trackAddToCart(product, quantity = 1) {
  trackItems('add_to_cart', { ...product, quantity })
}

export function trackRemoveFromCart(product, quantity) {
  trackItems('remove_from_cart', { ...product, quantity: quantity ?? product?.quantity ?? 1 })
}

export function trackAddToWishlist(product) {
  trackItems('add_to_wishlist', product)
}

export function trackViewCart(cartItems) {
  trackItems('view_cart', cartItems)
}

export function trackBeginCheckout(cartItems, paymentType) {
  trackItems('begin_checkout', cartItems, paymentType ? { payment_type: paymentType } : {})
}

function readTrackedPurchases() {
  try {
    return JSON.parse(readStorage(PURCHASE_STORAGE_KEY)) || []
  } catch {
    return []
  }
}

/**
 * Report a completed order once. Keyed on the Sales Order name so a refresh or a second
 * visit to the success page does not double-count revenue.
 */
export function trackPurchase({ transactionId, value, currency, shipping, items = [], paymentType }) {
  if (!isAnalyticsEnabled() || !transactionId) {
    return
  }

  const tracked = readTrackedPurchases()
  if (tracked.includes(transactionId)) {
    return
  }

  const gaItems = items.map((item, index) => toAnalyticsItem(item, { index }))
  track('purchase', {
    transaction_id: transactionId,
    currency: currency || DEFAULT_CURRENCY,
    value: Number(toNumber(value || itemsValue(gaItems)).toFixed(2)),
    ...(shipping ? { shipping: toNumber(shipping) } : {}),
    ...(paymentType ? { payment_type: paymentType } : {}),
    items: gaItems,
  })

  writeStorage(PURCHASE_STORAGE_KEY, JSON.stringify([...tracked, transactionId].slice(-50)))
}

export function trackSearch(searchTerm) {
  const term = String(searchTerm || '').trim()
  if (term) {
    track('search', { search_term: term })
  }
}

export function trackLogin(method = 'otp') {
  track('login', { method })
}
