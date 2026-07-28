export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

export const SITE_BASE_URL =
  import.meta.env.VITE_SITE_BASE_URL || API_BASE_URL.replace(/\/api\/?$/, '')

export const PRODUCT_API_PATH =
  import.meta.env.VITE_PRODUCT_API_PATH || '/method/buy_in_minutes.api.get_items'

export const GOOGLE_MAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || ''
