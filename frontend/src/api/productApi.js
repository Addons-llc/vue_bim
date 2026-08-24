import {
  getItemMasterCategories,
  getItemMasterItem,
  getItemMasterItems,
  getItemMasterVariants,
  searchItemMasterItems,
} from './itemApi'

let productCategoriesCache = []

export function getCachedProductCategories() {
  return productCategoriesCache
}

export function getProductCategories() {
  return getItemMasterCategories().then((categories) => {
    productCategoriesCache = categories
    return categories
  })
}

export function getProducts(params = {}) {
  return getItemMasterItems(params)
}

export function getProductById(productId) {
  return getItemMasterItem(productId)
}

export function getProductVariants(templateItemName) {
  return getItemMasterVariants(templateItemName)
}

export function searchProducts(searchText) {
  return searchItemMasterItems(searchText)
}
