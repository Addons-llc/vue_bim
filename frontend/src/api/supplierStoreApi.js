import {
  SITE_BASE_URL,
  SUPPLIER_STORE_API_PATH,
} from './config'
import { apiRequest } from './http'

const supplierStorePlaceholderImage = `${import.meta.env.BASE_URL}fresh-market-placeholder.svg?v=1`

function getImageUrl(imagePath) {
  if (!imagePath) {
    return ''
  }

  if (/^(https?:|data:|blob:)/.test(imagePath)) {
    return imagePath
  }

  if (!SITE_BASE_URL) {
    return imagePath
  }

  return imagePath.startsWith('/')
    ? `${SITE_BASE_URL}${imagePath}`
    : `${SITE_BASE_URL}/${imagePath}`
}

function getStoreProductIds(store = {}) {
  const productRows = [
    store.products,
    store.store_products,
    store.items,
    store.store_items,
    store.associated_products,
    store.product_items,
  ].find(Array.isArray) || []

  return productRows
    .map((row) =>
      row.item
      || row.item_code
      || row.item_name
      || row.product
      || row.product_code
      || row.name,
    )
    .filter(Boolean)
}

function mapSupplierStoreToBrand(store) {
  const storeName = store.store_name || store.name
  const storeLogo = store.store_logo
    || store.logo
    || store.supplier_logo
    || store.custom_store_logo
    || store.custom_supplier_logo
  const storeBanner = store.banner_image
    || store.store_banner
    || store.store_banner_image
    || store.supplier_banner
    || store.supplier_banner_image
    || store.custom_banner_image
    || store.custom_store_banner
    || store.custom_store_banner_image
    || store.custom_supplier_banner
    || store.custom_supplier_banner_image

  return {
    id: store.name || store.store_code || storeName,
    name: storeName,
    itemGroup: store.supplier || storeName,
    supplier: store.supplier || '',
    storeCode: store.store_code || store.name,
    storeStatus: store.store_status || '',
    isPublished: store.published === true || store.published === 1 || store.published === '1',
    image: getImageUrl(storeLogo || storeBanner) || supplierStorePlaceholderImage,
    bannerImage: getImageUrl(storeBanner),
    primaryColour: store.primary_colour || '',
    secondaryColour: store.secondary_colour || '',
    contactNumber: store.contact_number || '',
    whatsappNumber: store.whatsapp_number || '',
    email: store.email || store.contact_email || '',
    website: store.website || store.store_website || '',
    description: store.description || store.store_details || store.about || '',
    supplierDetails: store.supplier_details || '',
    sellerSince: store.seller_since || store.creation || '',
    productIds: getStoreProductIds(store),
  }
}

export async function getSupplierStores(params = {}) {
  const query = new URLSearchParams({
    limit_page_length: params.limit_page_length || 24,
    published: 1,
  })
  const response = await apiRequest(`${SUPPLIER_STORE_API_PATH}?${query.toString()}`)
  const stores = response.message || []

  return stores.map(mapSupplierStoreToBrand)
}

export async function getSupplierStore(identifier) {
  const stores = await getSupplierStores({
    limit_page_length: 5000,
  })
  const normalizedIdentifier = String(identifier || '').toLowerCase()

  return stores.find((store) =>
    [
      store.id,
      store.name,
      store.supplier,
      store.storeCode,
    ].some((value) => String(value || '').toLowerCase() === normalizedIdentifier),
  ) || null
}
