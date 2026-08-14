import {
  BRAND_API_PATH,
  SITE_BASE_URL,
} from './config'
import { apiRequest } from './http'

const brandPlaceholderImage = `${import.meta.env.BASE_URL}grocery-card-image-v3.svg?v=3`

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

function stripHtml(value = '') {
  return value.replace(/<[^>]*>/g, '').trim()
}

function mapBrand(brand = {}) {
  const brandName = brand.brand || brand.name
  const image = getImageUrl(
    brand.image
      || brand.brand_image
      || brand.website_image
      || brand.logo
      || brand.brand_logo,
  ) || brandPlaceholderImage

  return {
    id: brand.name || brandName,
    name: brandName,
    brand: brand.name || brandName,
    description: stripHtml(brand.description || ''),
    image,
    bannerImage: getImageUrl(brand.banner_image || brand.brand_banner),
  }
}

export async function getBrands(params = {}) {
  const query = new URLSearchParams({
    limit_page_length: params.limit_page_length || 24,
    published: 1,
  })
  const response = await apiRequest(`${BRAND_API_PATH}?${query.toString()}`)
  const brands = response.message || []

  return brands.map(mapBrand)
}

export async function getBrand(identifier) {
  const brands = await getBrands({
    limit_page_length: 5000,
  })
  const normalizedIdentifier = String(identifier || '').toLowerCase()

  return brands.find((brand) =>
    [
      brand.id,
      brand.name,
      brand.brand,
    ].some((value) => String(value || '').toLowerCase() === normalizedIdentifier),
  ) || null
}
