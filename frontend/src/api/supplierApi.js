import { apiRequest } from './http'
import { SITE_BASE_URL } from './config'

function stripHtml(value = '') {
  return value.replace(/<[^>]*>/g, '').trim()
}

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

function mapSupplierDetails(supplier = {}) {
  const supplierName = supplier.name || supplier.supplier_name || ''

  return {
    name: supplier.name || supplierName,
    displayName: supplier.supplier_name || supplierName,
    supplier: supplier.name || supplierName,
    details: stripHtml(supplier.supplier_details || ''),
    group: supplier.supplier_group || '',
    type: supplier.supplier_type || '',
    phone: supplier.mobile_no || '',
    email: supplier.email_id || '',
    website: supplier.website || '',
    image: getImageUrl(
      supplier.image
        || supplier.supplier_logo
        || supplier.supplier_image
        || supplier.custom_supplier_logo
        || supplier.custom_supplier_image,
    ),
    customGoogleAddress: supplier.custom_google_address || supplier.customGoogleAddress || '',
    bannerImage: getImageUrl(
      supplier.supplier_banner
        || supplier.supplier_banner_image
        || supplier.custom_supplier_banner
        || supplier.custom_supplier_banner_image,
    ),
    sellerSince: supplier.custom_seller_since || '',
  }
}

export function createSupplier(supplier) {
  return apiRequest('/resource/Supplier', {
    method: 'POST',
    body: JSON.stringify({
      supplier_name: supplier.supplierName,
      supplier_group: supplier.supplierGroup,
      supplier_type: supplier.supplierType,
      website: supplier.website,
      supplier_details: supplier.supplierDetails,
    }),
  })
}

export async function getSupplierDetails(supplierName) {
  const query = new URLSearchParams({
    supplier: supplierName,
  })
  const response = await apiRequest(
    `/method/buy_in_minutes.api.get_supplier_details?${query.toString()}`,
  )

  return response.message?.name ? mapSupplierDetails(response.message) : null
}
