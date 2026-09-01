import { apiRequest } from './http'

function normalizeOrderHistoryItem(item = {}) {
  return {
    id: String(item.id || item.product_id || item.item_code || ''),
    productId: String(item.product_id || item.item_code || item.id || ''),
    itemCode: String(item.item_code || item.product_id || item.id || ''),
    itemName: String(item.item_name || item.name || ''),
    description: String(item.description || ''),
    qty: Number(item.qty || 0),
    rate: Number(item.rate || 0),
    amount: Number(item.amount || 0),
    image: String(item.image || ''),
  }
}

function normalizeOrderHistoryOrder(order = {}) {
  const items = Array.isArray(order.items)
    ? order.items.map(normalizeOrderHistoryItem)
    : []

  return {
    name: String(order.name || ''),
    status: String(order.status || ''),
    transactionDate: order.transaction_date || '',
    transaction_date: order.transaction_date || '',
    grandTotal: Number(order.grand_total || 0),
    grand_total: Number(order.grand_total || 0),
    currency: String(order.currency || 'AED'),
    customer: String(order.customer || ''),
    customerName: String(order.customer_name || order.customer || ''),
    customer_name: String(order.customer_name || order.customer || ''),
    purchaseOrders: Array.isArray(order.purchase_orders) ? order.purchase_orders : [],
    purchase_orders: Array.isArray(order.purchase_orders) ? order.purchase_orders : [],
    items,
  }
}

export async function getOrderHistory() {
  const response = await apiRequest('/method/buy_in_minutes.order_history.get_order_history')
  const orders = Array.isArray(response?.message)
    ? response.message.map(normalizeOrderHistoryOrder)
    : []

  return {
    ...response,
    message: orders,
  }
}
