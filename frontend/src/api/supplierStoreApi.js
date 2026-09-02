import {
  SITE_BASE_URL,
  SUPPLIER_STORE_API_PATH,
} from './config'
import { apiRequest } from './http'

const supplierStorePlaceholderImage = `${import.meta.env.BASE_URL}fresh-market-placeholder.svg?v=1`
const SUPPLIER_WEBSITE_BASE_URL = 'https://buyinminutes.u.frappe.cloud/supplier-website'

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

function normalizeWebsiteUrl(url) {
  const value = String(url || '').trim()

  if (!value) {
    return ''
  }

  if (/^(https?:|data:|blob:)/i.test(value)) {
    return value
  }

  if (value.startsWith('/')) {
    return `${SITE_BASE_URL}${value}`
  }

  return `https://${value}`
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
    || store.store_image
    || store.logo
    || store.image
    || store.website_image
    || store.supplier_image
    || store.supplier_logo
    || store.custom_store_logo
    || store.custom_supplier_logo
  const storeBanner = store.banner_image
    || store.banner
    || store.store_banner
    || store.store_banner_image
    || store.store_cover
    || store.store_cover_image
    || store.cover_image
    || store.cover_photo
    || store.website_banner
    || store.website_banner_image
    || store.supplier_banner
    || store.supplier_banner_image
    || store.custom_banner_image
    || store.custom_store_banner
    || store.custom_store_banner_image
    || store.custom_store_cover
    || store.custom_store_cover_image
    || store.custom_cover_image
    || store.custom_cover_photo
    || store.custom_website_banner
    || store.custom_website_banner_image
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
    contactNumber: store.contact_number
      || store.phone
      || store.mobile_no
      || store.contact_mobile
      || store.store_phone
      || store.store_contact_number
      || store.custom_contact_number
      || '',
    whatsappNumber: store.whatsapp_number || '',
    email: store.email
      || store.contact_email
      || store.store_email
      || store.custom_email
      || store.custom_contact_email
      || '',
    website: store.website
      || store.store_website
      || store.website_url
      || store.custom_website
      || store.custom_store_website
      || '',
    shortDescription: store.short_description || '',
    description: store.short_description || store.description || store.store_details || store.about || '',
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

async function getSupplierWebsiteProfileUrlByStoreValue(supplierStore) {
  const filters = encodeURIComponent(JSON.stringify([
    ['supplier_store', '=', supplierStore],
  ]))
  const fields = encodeURIComponent(JSON.stringify(['name', 'supplier', 'supplier_name', 'supplier_store', 'slug']))
  const response = await apiRequest(
    `/resource/Supplier Website Profile?fields=${fields}&filters=${filters}&limit_page_length=1`,
  )
  const profile = response.data?.[0]

  return buildSupplierPortalUrlFromSlug(profile?.slug)
}

async function getSupplierWebsiteProfileBySupplier(supplier) {
  const filters = encodeURIComponent(JSON.stringify([
    ['supplier', '=', supplier],
  ]))
  const fields = encodeURIComponent(JSON.stringify(['name', 'supplier', 'supplier_name', 'supplier_store', 'slug']))
  const response = await apiRequest(
    `/resource/Supplier Website Profile?fields=${fields}&filters=${filters}&limit_page_length=1`,
  )

  return response.data?.[0] || null
}

function buildSupplierPortalUrlFromSlug(slug) {
  const normalizedSlug = String(slug || '').trim().replace(/^\/+|\/+$/g, '')

  if (!normalizedSlug) {
    return ''
  }

  return `${SUPPLIER_WEBSITE_BASE_URL}/${normalizedSlug}`
}

export async function getSupplierStorePortalUrl(storeIdentifier, supplierName = '') {
  const normalizedSupplierName = String(supplierName || '').trim()
  const profile = normalizedSupplierName
    ? await getSupplierWebsiteProfileBySupplier(normalizedSupplierName).catch(() => null)
    : null

  if (profile) {
    return buildSupplierPortalUrlFromSlug(profile.slug)
  }

  if (!storeIdentifier) {
    return ''
  }

  const store = await getSupplierStore(storeIdentifier).catch(() => null)
  const candidateStoreValues = [
    store?.storeCode,
    store?.id,
    store?.name,
    store?.supplier,
    storeIdentifier,
  ].filter(Boolean)

  for (const supplierStore of [...new Set(candidateStoreValues)]) {
    const portalUrl = await getSupplierWebsiteProfileUrlByStoreValue(supplierStore).catch(() => '')

    if (portalUrl) {
      return portalUrl
    }
  }

  return ''
}
