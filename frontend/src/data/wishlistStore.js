import { computed, ref } from 'vue'

const WISHLIST_STORAGE_KEY = 'buyInMinutesWishlist'

function readStoredWishlist() {
  try {
    return JSON.parse(localStorage.getItem(WISHLIST_STORAGE_KEY)) || []
  } catch {
    return []
  }
}

function saveWishlist(items) {
  localStorage.setItem(WISHLIST_STORAGE_KEY, JSON.stringify(items))
}

const wishlistItems = ref(readStoredWishlist())

export const wishlistProducts = wishlistItems

export const wishlistItemCount = computed(() => wishlistItems.value.length)

export function isProductWishlisted(productId) {
  return wishlistItems.value.some((item) => item.id === productId)
}

export function toggleProductWishlist(product) {
  if (!product?.id) {
    return false
  }

  if (isProductWishlisted(product.id)) {
    wishlistItems.value = wishlistItems.value.filter((item) => item.id !== product.id)
    saveWishlist(wishlistItems.value)
    return false
  }

  wishlistItems.value.push({
    id: product.id,
    itemCode: product.itemCode || product.id,
    name: product.name,
    price: product.price,
    oldPrice: product.oldPrice,
    description: product.description,
    image: product.image,
    supplierName: product.supplierName,
    supplier: product.supplier,
    category: product.category,
    rating: product.rating,
    reviewCount: product.reviewCount,
    deliveryTime: product.deliveryTime,
    inStock: product.inStock,
    stockQuantity: product.stockQuantity,
    supplierDetails: product.supplierDetails,
    images: product.images,
    details: product.details,
  })
  saveWishlist(wishlistItems.value)

  return true
}

export function clearWishlist() {
  wishlistItems.value = []
  saveWishlist(wishlistItems.value)
}
