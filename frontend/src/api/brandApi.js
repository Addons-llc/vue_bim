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

function getBrandProductCount(brand = {}) {
  const productRows = [
    brand.products,
    brand.brand_products,
    brand.items,
    brand.brand_items,
    brand.product_items,
  ].find(Array.isArray)

  if (productRows) {
    return productRows.length
  }

  const count = brand.product_count
    ?? brand.products_count
    ?? brand.item_count
    ?? brand.items_count
    ?? brand.total_products
    ?? brand.total_items

  return Number.isFinite(Number(count)) ? Number(count) : null
}

function mapBrand(brand = {}) {
  const brandName = brand.brand || brand.name
  const bannerImage = getImageUrl(
    brand.banner
      || brand.banner_image
      || brand.brand_banner
      || brand.brand_banner_image
      || brand.website_banner
      || brand.website_banner_image
      || brand.cover_image
      || brand.cover_photo
      || brand.custom_banner
      || brand.custom_banner_image
      || brand.custom_brand_banner
      || brand.custom_brand_banner_image
      || brand.custom_website_banner
      || brand.custom_website_banner_image
      || brand.custom_cover_image
      || brand.custom_cover_photo,
  )
  const bannerImages = [
    brand.custom_brand_banner_image,
    brand.custom_brand_banner_image_2,
    brand.custom_brand_banner_image_3,
  ]
    .map((imagePath) => getImageUrl(imagePath))
    .filter(Boolean)
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
    bannerImage,
    bannerImages: bannerImages.length ? bannerImages : (bannerImage ? [bannerImage] : []),
    rating: brand.rating || brand.average_rating || brand.review_rating || '',
    productCount: getBrandProductCount(brand),
    offerBadge: brand.offer_badge
      || brand.offer
      || brand.discount_label
      || brand.promo_label
      || brand.brand_offer
      || 'Offer',
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
