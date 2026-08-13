import {
  getItemMasterCategories,
  getItemMasterItem,
  getItemMasterItems,
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

export function searchProducts(searchText) {
  return searchItemMasterItems(searchText)
}
