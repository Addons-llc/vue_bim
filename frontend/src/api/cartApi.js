import { apiRequest } from './http'

export function getCart() {
  return apiRequest('/cart')
}

export function addToCart(productId, quantity = 1) {
  return apiRequest('/cart/items', {
    method: 'POST',
    body: JSON.stringify({ productId, quantity }),
  })
}

export function updateCartItem(cartItemId, quantity) {
  return apiRequest(`/cart/items/${cartItemId}`, {
    method: 'PATCH',
    body: JSON.stringify({ quantity }),
  })
}

export function removeCartItem(cartItemId) {
  return apiRequest(`/cart/items/${cartItemId}`, {
    method: 'DELETE',
  })
}
