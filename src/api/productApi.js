import {
  getItemMasterItem,
  getItemMasterItems,
  searchItemMasterItems,
} from './itemApi'

export function getProducts(params = {}) {
  return getItemMasterItems(params)
}

export function getProductById(productId) {
  return getItemMasterItem(productId)
}

export function searchProducts(searchText) {
  return searchItemMasterItems(searchText)
}
