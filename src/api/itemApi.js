import { PRODUCT_API_PATH, SITE_BASE_URL } from './config'
import { getDocTypeByName } from './frappeResource'
import { apiRequest } from './http'

const fallbackImages = {
  bakery:
    'https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=400&q=80',
  beverages:
    'https://images.unsplash.com/photo-1622483767028-3f66f32aef97?auto=format&fit=crop&w=400&q=80',
  dairy:
    'https://images.unsplash.com/photo-1628088062854-d1870b4553da?auto=format&fit=crop&w=400&q=80',
  fruits:
    'https://images.unsplash.com/photo-1610832958506-aa56368176cf?auto=format&fit=crop&w=400&q=80',
  grocery:
    'https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=400&q=80',
  meat:
    'https://images.unsplash.com/photo-1607623814075-e51df1bdc82f?auto=format&fit=crop&w=400&q=80',
  snacks:
    'https://images.unsplash.com/photo-1621939514649-280e2ee25f60?auto=format&fit=crop&w=400&q=80',
  vegetables:
    'https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=400&q=80',
}

function stripHtml(value = '') {
  return value.replace(/<[^>]*>/g, '').trim()
}

function toNumber(value) {
  const numberValue = Number(value)

  return Number.isFinite(numberValue) ? numberValue : 0
}

function getImageUrl(imagePath) {
  if (!imagePath) {
    return ''
  }

  return imagePath.startsWith('/') && SITE_BASE_URL
    ? `${SITE_BASE_URL}${imagePath}`
    : imagePath
}

function getFallbackImage(itemGroup = '') {
  const normalizedItemGroup = itemGroup.toLowerCase()
  const fallbackKey = Object.keys(fallbackImages).find((key) =>
    normalizedItemGroup.includes(key),
  )

  return fallbackImages[fallbackKey] || fallbackImages.grocery
}

function mapItemToProduct(item) {
  const itemGroup = item.item_group || 'Grocery'
  const image = getImageUrl(item.image || item.website_image || item.thumbnail)
    || getFallbackImage(itemGroup)
  const description = stripHtml(item.description || '')
  const itemCode = item.item_code || item.name

  return {
    id: item.name,
    itemCode,
    name: item.item_name || itemCode,
    category: itemGroup,
    description: description || 'Fresh item available for quick delivery.',
    price: toNumber(item.standard_rate),
    oldPrice: null,
    rating: 4.8,
    deliveryTime: '18 min',
    image,
    imageLabel: item.item_group || 'Item',
  }
}

export async function getItemMasterItems(params = {}) {
  const query = new URLSearchParams({
    limit_page_length: params.limit_page_length || 20,
  })

  if (params.search) {
    query.set('search', params.search)
  }

  if (params.item_group) {
    query.set('item_group', params.item_group)
  }

  const response = await apiRequest(
    `${PRODUCT_API_PATH}?${query.toString()}`,
  )
  const items = response.message || []

  return items.map(mapItemToProduct)
}

export async function getItemMasterItem(itemName) {
  const item = await getDocTypeByName('Item', itemName)

  return mapItemToProduct(item)
}

export async function searchItemMasterItems(searchText) {
  return getItemMasterItems({
    search: searchText,
  })
}
