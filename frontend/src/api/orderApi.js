import { apiRequest } from './http'

export function syncCartSalesOrder(cartItems, salesOrderName = '') {
  return apiRequest('/method/buy_in_minutes.payment.sync_cart_sales_order', {
    method: 'POST',
    body: JSON.stringify({
      cart_items: cartItems.map((item) => ({
        id: item.id,
        item_code: item.itemCode || item.id,
        quantity: item.quantity,
      })),
      sales_order_name: salesOrderName,
    }),
  })
}

export function getOrders() {
  return apiRequest('/orders')
}

export function getOrderById(orderId) {
  return apiRequest(`/orders/${orderId}`)
}

export function getSalesOrder(salesOrderName) {
  const query = new URLSearchParams({
    sales_order_name: salesOrderName,
  })

  return apiRequest(`/method/buy_in_minutes.api.get_sales_order?${query.toString()}`)
}

export function getOrderedProducts() {
  return apiRequest('/method/buy_in_minutes.api.get_ordered_products')
}

export function createOrder(orderData) {
  return apiRequest('/orders', {
    method: 'POST',
    body: JSON.stringify(orderData),
  })
}
