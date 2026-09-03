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
  const historyType = String(order.history_type || 'sales_order')

  return {
    name: String(order.name || ''),
    title: String(order.title || order.name || ''),
    historyType,
    history_type: historyType,
    status: String(order.status || ''),
    transactionDate: order.transaction_date || '',
    transaction_date: order.transaction_date || '',
    requiredDate: order.required_date || '',
    required_date: order.required_date || '',
    validTill: order.valid_till || '',
    valid_till: order.valid_till || '',
    grandTotal: Number(order.grand_total || 0),
    grand_total: Number(order.grand_total || 0),
    currency: String(order.currency || 'AED'),
    customer: String(order.customer || ''),
    customerName: String(order.customer_name || order.customer || ''),
    customer_name: String(order.customer_name || order.customer || ''),
    supplier: String(order.supplier || ''),
    supplierName: String(order.supplier_name || order.supplier || ''),
    supplier_name: String(order.supplier_name || order.supplier || ''),
    purchaseOrders: Array.isArray(order.purchase_orders) ? order.purchase_orders : [],
    purchase_orders: Array.isArray(order.purchase_orders) ? order.purchase_orders : [],
    company: String(order.company || ''),
    billingAddress: String(order.billing_address || ''),
    billing_address: String(order.billing_address || ''),
    billingAddressDisplay: String(order.billing_address_display || ''),
    billing_address_display: String(order.billing_address_display || ''),
    contactDisplay: String(order.contact_display || ''),
    contact_display: String(order.contact_display || ''),
    contactMobile: String(order.contact_mobile || ''),
    contact_mobile: String(order.contact_mobile || ''),
    contactEmail: String(order.contact_email || ''),
    contact_email: String(order.contact_email || ''),
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

export async function confirmSupplierQuotationOrder(supplierQuotationName, deliveryAddress = null) {
  const response = await apiRequest('/method/buy_in_minutes.payment.confirm_supplier_quotation_order', {
    method: 'POST',
    body: JSON.stringify({
      supplier_quotation_name: String(supplierQuotationName || '').trim(),
      delivery_address: deliveryAddress,
    }),
  })

  return response?.message || null
}
