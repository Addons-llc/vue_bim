import { apiRequest } from './http'

export function getOrders() {
  return apiRequest('/orders')
}

export function getOrderById(orderId) {
  return apiRequest(`/orders/${orderId}`)
}

export function createOrder(orderData) {
  return apiRequest('/orders', {
    method: 'POST',
    body: JSON.stringify(orderData),
  })
}
