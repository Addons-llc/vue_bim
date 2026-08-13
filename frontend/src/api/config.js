function getCurrentOrigin() {
  return typeof window !== 'undefined' && window.location?.origin
    ? window.location.origin
    : 'https://addons-bim.m.frappe.cloud'
}

export const SITE_BASE_URL =
  import.meta.env.VITE_SITE_BASE_URL || getCurrentOrigin()

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || `${SITE_BASE_URL}/api`

export const PRODUCT_API_PATH =
  import.meta.env.VITE_PRODUCT_API_PATH || '/method/buy_in_minutes.api.get_items'

export const ITEM_GROUP_API_PATH =
  import.meta.env.VITE_ITEM_GROUP_API_PATH || '/method/buy_in_minutes.api.get_item_groups'

export const SUPPLIER_STORE_API_PATH =
  import.meta.env.VITE_SUPPLIER_STORE_API_PATH || '/method/buy_in_minutes.api.get_supplier_stores'

export const SELLING_PRICE_LIST =
  import.meta.env.VITE_SELLING_PRICE_LIST || 'Selling Price'

export const GOOGLE_MAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || ''
