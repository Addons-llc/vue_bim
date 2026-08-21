import {
  ITEM_GROUP_API_PATH,
  PRODUCT_API_PATH,
  SELLING_PRICE_LIST,
  SITE_BASE_URL,
} from './config'
import { getEstimatedDeliveryTimeLabel } from './deliveryEta'
import { getDocTypeByName, getDocTypeList } from './frappeResource'
import { apiRequest } from './http'

const categoryPlaceholderImage = `${import.meta.env.BASE_URL}grocery-card-image-v3.svg?v=3`

function stripHtml(value = '') {
  return value.replace(/<[^>]*>/g, '').trim()
}

function toNumber(value) {
  const numberValue = Number(value)

  return Number.isFinite(numberValue) ? numberValue : 0
}

function getStockQuantity(item) {
  return toNumber(item.actual_qty ?? item.projected_qty ?? item.stock_qty ?? item.qty_available)
}

function getReviewCount(item) {
  return toNumber(item.review_count ?? item.reviews_count ?? item.total_reviews)
}

function getSupplierName(item) {
  return (
    item.supplier_name
    || item.supplier
    || item.default_supplier
    || item.custom_supplier_name
    || item.custom_supplier
    || ''
  )
}

function getSupplierDetails(item) {
  return {
    name: getSupplierName(item),
    displayName: item.supplier_display_name || item.custom_supplier_display_name || getSupplierName(item),
    details: stripHtml(
      item.supplier_details
        || item.custom_supplier_details
        || item.supplier_description
        || item.custom_supplier_description
        || '',
    ),
    group: item.supplier_group || item.custom_supplier_group || '',
    type: item.supplier_type || item.custom_supplier_type || '',
    phone: item.supplier_phone || item.supplier_mobile || item.custom_supplier_phone || '',
    email: item.supplier_email || item.custom_supplier_email || '',
    website: item.supplier_website || item.custom_supplier_website || '',
    image: getImageUrl(
      item.supplier_image
        || item.supplier_logo
        || item.custom_supplier_image
        || item.custom_supplier_logo,
    ),
    customGoogleAddress: item.custom_google_address || item.customGoogleAddress || '',
    customLatitude: item.custom_latitude || item.customLatitude || item.supplier_custom_latitude || '',
    customLongitude: item.custom_longitude || item.customLongitude || item.supplier_custom_longitude || '',
    bannerImage: getImageUrl(
      item.supplier_banner
        || item.supplier_banner_image
        || item.custom_supplier_banner
        || item.custom_supplier_banner_image,
    ),
    sellerSince: item.seller_since || item.supplier_since || item.custom_seller_since || '',
  }
}

function getItemSellingPrice(item) {
  return toNumber(
    item.selling_price
      ?? item.price_list_rate
      ?? item.item_price
      ?? item.rate
      ?? item.standard_rate,
  )
}

function isTruthyFlag(value) {
  return value === true || value === 1 || value === '1' || value === 'Yes'
}

function hasCustomDeliverySlots(item) {
  return isTruthyFlag(
    item.custom_delivery_slots
      ?? item.customDeliverySlots
      ?? item.delivery_slots
      ?? item.deliverySlots,
  )
}

function hasPublishField(item) {
  return [
    'published_in_supplier_portal',
    'custom_published_in_supplier_portal',
    'published',
    'is_published',
    'show_in_website',
    'custom_published',
    'custom_is_published',
    'custom_show_in_website',
  ].some((field) => Object.hasOwn(item, field))
}

function isPublishedItem(item) {
  if (!hasPublishField(item)) {
    return true
  }

  return [
    item.published_in_supplier_portal,
    item.custom_published_in_supplier_portal,
    item.published,
    item.is_published,
    item.show_in_website,
    item.custom_published,
    item.custom_is_published,
    item.custom_show_in_website,
  ].some(isTruthyFlag)
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

function getFallbackImage() {
  return categoryPlaceholderImage
}

function getItemGroupImage(item) {
  return getImageUrl(
    item.profile_image
      || item.category_profile_image
      || item.item_group_profile_image
      || item.item_group_image
      || item.item_group_website_image
      || item.category_image
      || item.group_image
      || item.item_group_photo,
  )
}

function getItemBannerImage(item) {
  return getImageUrl(
    item.banner_image
      || item.item_banner_image
      || item.website_banner_image
      || item.product_banner_image
      || item.custom_banner_image
      || item.custom_item_banner_image
      || item.custom_product_banner_image,
  )
}

function getItemSize(item) {
  return stripHtml(
    item.custom_size
      || item.customSize
      || item.custom_size_options
      || item.custom_sizes
      || '',
  )
}

function getAttachmentFieldValue(record) {
  if (!record || typeof record !== 'object') {
    return ''
  }

  return getImageUrl(
    record.image
      || record.image_url
      || record.image_path
      || record.attachment
      || record.attachment_url
      || record.file
      || record.file_url
      || record.file_name
      || record.url
      || record.photo
      || record.thumbnail,
  )
}

function getItemAttachmentImages(item) {
  const images = []
  const seenImages = new Set()
  const imageFieldPattern = /(attachment|attachments|gallery|slider|carousel|image)/i
  const pushImage = (image) => {
    const imageUrl = getImageUrl(image)

    if (!imageUrl || seenImages.has(imageUrl)) {
      return
    }

    seenImages.add(imageUrl)
    images.push(imageUrl)
  }

  const primaryImageCandidates = [
    item.image,
    item.website_image,
    item.thumbnail,
    item.banner_image,
    item.item_banner_image,
    item.website_banner_image,
    item.product_banner_image,
    item.custom_banner_image,
    item.custom_item_banner_image,
    item.custom_product_banner_image,
  ]

  primaryImageCandidates.forEach(pushImage)

  Object.entries(item || {}).forEach(([fieldname, value]) => {
    if (!imageFieldPattern.test(fieldname)) {
      return
    }

    if (typeof value === 'string') {
      pushImage(value)
      return
    }

    if (!Array.isArray(value)) {
      return
    }

    value.forEach((entry) => {
      if (typeof entry === 'string') {
        pushImage(entry)
        return
      }

      const imageUrl = getAttachmentFieldValue(entry)

      if (imageUrl) {
        pushImage(imageUrl)
      }
    })
  })

  return images.slice(0, 3)
}

async function mapItemToProduct(item) {
  const itemGroup = item.item_group || ''
  const categoryImage = getItemGroupImage(item)
  const bannerImage = getItemBannerImage(item)
  const image = getImageUrl(item.image || item.website_image || item.thumbnail)
    || getFallbackImage(itemGroup)
  const description = stripHtml(item.description || '')
  const customSize = getItemSize(item)
  const itemCode = item.item_code || item.name
  const stockQuantity = getStockQuantity(item)
  const reviewCount = getReviewCount(item)
  const supplierDetails = getSupplierDetails(item)
  const images = getItemAttachmentImages(item)
  const deliveryTime = await getEstimatedDeliveryTimeLabel({
    supplierDetails,
  })

  return {
    id: item.name,
    itemCode,
    name: item.item_name || itemCode,
    category: itemGroup,
    brand: item.brand || '',
    customPopularItems: isTruthyFlag(item.custom_popular_items),
    customDeliverySlots: hasCustomDeliverySlots(item),
    description: description || '',
    customSize,
    price: getItemSellingPrice(item),
    priceList: item.price_list || SELLING_PRICE_LIST,
    currency: item.currency || 'AED',
    oldPrice: null,
    rating: toNumber(item.rating ?? item.average_rating) || 4.8,
    reviewCount,
    supplier: supplierDetails.name,
    supplierName: supplierDetails.displayName || supplierDetails.name,
    supplierDetails,
    stockQuantity,
    inStock: stockQuantity > 0 || item.disabled === 0,
    isPublished: isPublishedItem(item),
    deliveryTime,
    image,
    bannerImage,
    images,
    categoryImage,
    imageLabel: item.item_group || 'Item',
  }
}

function mapItemGroupToCategory(itemGroup) {
  const itemGroupName = itemGroup.name || itemGroup.item_group_name
  const displayName = itemGroup.item_group_name || itemGroupName
  const parentItemGroup = itemGroup.parent_item_group
    || itemGroup.parent
    || itemGroup.parent_item_group_name
    || ''
  const image = getImageUrl(
    itemGroup.profile_image
      || itemGroup.category_profile_image
      || itemGroup.item_group_profile_image
      || itemGroup.image
      || itemGroup.website_image
      || itemGroup.item_group_image
      || itemGroup.item_group_website_image,
  ) || getFallbackImage()

  return {
    id: itemGroupName,
    name: displayName,
    itemGroup: itemGroupName,
    parentItemGroup,
    isGroup: isTruthyFlag(itemGroup.is_group),
    rating: itemGroup.rating || itemGroup.average_rating || itemGroup.review_rating || '',
    productCount: Number(
      itemGroup.product_count
        ?? itemGroup.products_count
        ?? itemGroup.item_count
        ?? itemGroup.items_count
        ?? itemGroup.total_products
        ?? itemGroup.total_items,
    ) || null,
    isPublished: isPublishedItem(itemGroup),
    image,
  }
}

export async function getItemMasterItems(params = {}) {
  const query = new URLSearchParams({
    limit_page_length: params.limit_page_length || 20,
    published: 1,
  })

  if (params.limit_start) {
    query.set('limit_start', params.limit_start)
  }

  if (params.search) {
    query.set('search', params.search)
  }

  if (params.item_group) {
    query.set('item_group', params.item_group)
  }

  if (params.item) {
    query.set('item', params.item)
  }

  if (params.brand) {
    query.set('brand', params.brand)
  }

  if (params.supplier) {
    query.set('supplier', params.supplier)
  }

  if (params.supplier_store) {
    query.set('supplier_store', params.supplier_store)
  }

  const response = await apiRequest(`${PRODUCT_API_PATH}?${query.toString()}`)
  const items = response.message || []

  return Promise.all(
    items
      .filter(isPublishedItem)
      .map(mapItemToProduct),
  )
}

export async function getItemMasterItem(itemName) {
  let listedProduct = null

  try {
    const products = await getItemMasterItems({
      item: itemName,
      limit_page_length: 1,
    })

    if (products.length) {
      listedProduct = products[0]
    }
  } catch {
    // Fall back to direct doctype read for older backend deployments.
  }

  try {
    const item = await getDocTypeByName('Item', itemName)
    if (!isPublishedItem(item)) {
      return null
    }

    const detailedProduct = await mapItemToProduct(item)

    return listedProduct
      ? {
        ...listedProduct,
        ...detailedProduct,
        image: detailedProduct.image || listedProduct.image,
        bannerImage: detailedProduct.bannerImage || listedProduct.bannerImage,
        images: detailedProduct.images?.length ? detailedProduct.images : (listedProduct.images || []),
      }
      : detailedProduct
  } catch (error) {
    if (listedProduct) {
      return listedProduct
    }

    throw error
  }
}

export async function getItemMasterCategories() {
  try {
    const itemGroups = await getDocTypeList('Item Group', {
      fields: [
        'name',
        'item_group_name',
        'parent_item_group',
        'is_group',
        'image',
      ],
      filters: [
        ['Item Group', 'name', '!=', 'All Item Groups'],
      ],
      order_by: 'lft asc',
      limit_page_length: 5000,
    })

    return itemGroups
      .filter(isPublishedItem)
      .map(mapItemGroupToCategory)
  } catch (error) {
    const query = new URLSearchParams({
      limit_page_length: 5000,
      published: 1,
    })
    const response = await apiRequest(`${ITEM_GROUP_API_PATH}?${query.toString()}`)
    const itemGroups = response.message || []

    return itemGroups
      .filter(isPublishedItem)
      .map(mapItemGroupToCategory)
  }
}

export async function searchItemMasterItems(searchText) {
  return getItemMasterItems({
    search: searchText,
  })
}
