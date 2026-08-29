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

function getFirstImageUrl(brand = {}, fieldNames = []) {
  const imagePath = fieldNames.find((fieldName) => brand[fieldName])
  return getImageUrl(imagePath ? brand[imagePath] : '')
}

function getBrandBannerImages(brand = {}) {
  return [
    'custom_brand_banner_image',
    'custom_brand_banner_image_2',
    'custom_brand_banner_image_3',
    'banner',
    'banner_image',
    'custom_banner_image',
    'brand_banner',
    'brand_banner_image',
    'website_banner',
    'website_banner_image',
    'cover_image',
    'cover_photo',
    'custom_brand_banner',
    'custom_website_banner',
    'custom_website_banner_image',
    'custom_cover_image',
    'custom_cover_photo',
    'banner_2',
    'banner_image_2',
    'brand_banner_2',
    'custom_banner_image_2',
    'custom_banner_2',
    'brand_banner_image_2',
    'website_banner_2',
    'website_banner_image_2',
    'custom_brand_banner_2',
    'banner_3',
    'banner_image_3',
    'brand_banner_3',
    'custom_banner_3',
    'custom_banner_image_3',
    'website_banner_3',
    'brand_banner_image_3',
    'website_banner_image_3',
    'custom_brand_banner_3',
  ]
    .map((fieldName) => getImageUrl(brand[fieldName]))
    .filter(Boolean)
    .filter((imagePath, index, imagePaths) => imagePaths.indexOf(imagePath) === index)
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
  const primaryBannerImage = getImageUrl(brand.custom_brand_banner_image || '')
  const secondaryBannerImage = getImageUrl(brand.custom_brand_banner_image_2 || '')
  const tertiaryBannerImage = getImageUrl(brand.custom_brand_banner_image_3 || '')
  const bannerImage = getFirstImageUrl(brand, [
    'banner',
    'banner_image',
    'brand_banner',
    'brand_banner_image',
    'website_banner',
    'website_banner_image',
    'cover_image',
    'cover_photo',
    'custom_banner',
    'custom_banner_image',
    'custom_brand_banner',
    'custom_brand_banner_image',
    'custom_website_banner',
    'custom_website_banner_image',
    'custom_cover_image',
    'custom_cover_photo',
  ])
  const bannerImages = getBrandBannerImages(brand)
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
    primaryBannerImage,
    secondaryBannerImage,
    tertiaryBannerImage,
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
  const matchedBrand = brands.find((brand) =>
    [
      brand.id,
      brand.name,
      brand.brand,
    ].some((value) => String(value || '').toLowerCase() === normalizedIdentifier),
  ) || null

  console.log('Brand banner fetch response', {
    identifier,
    matchedBrand,
    banners: matchedBrand?.bannerImages || [],
  })

  return matchedBrand
}
