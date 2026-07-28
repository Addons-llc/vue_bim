import { apiRequest } from './http'

export function getCategories() {
  return apiRequest('/categories')
}

export function getCategoryProducts(categoryId) {
  return apiRequest(`/categories/${categoryId}/products`)
}
