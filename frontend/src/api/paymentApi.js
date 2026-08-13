import { apiRequest } from './http'

export function createStripeCheckoutSession(cartItems, salesOrderName = '') {
  return apiRequest('/method/buy_in_minutes.payment.create_checkout_session', {
    method: 'POST',
    body: JSON.stringify({
      cart_items: cartItems.map((item) => ({
        id: item.id,
        item_code: item.itemCode || item.id,
        quantity: item.quantity,
        supplier: item.supplier || '',
        supplier_name: item.supplierName || '',
      })),
      sales_order_name: salesOrderName,
    }),
  })
}

export function createCashOnDeliveryOrder(cartItems, salesOrderName = '') {
  return apiRequest('/method/buy_in_minutes.payment.create_cash_on_delivery_order', {
    method: 'POST',
    body: JSON.stringify({
      cart_items: cartItems.map((item) => ({
        id: item.id,
        item_code: item.itemCode || item.id,
        quantity: item.quantity,
        supplier: item.supplier || '',
        supplier_name: item.supplierName || '',
      })),
      sales_order_name: salesOrderName,
    }),
  })
}

export function finalizeStripeCheckout(sessionId) {
  return apiRequest('/method/buy_in_minutes.payment.finalize_stripe_checkout', {
    method: 'POST',
    body: JSON.stringify({
      session_id: sessionId,
    }),
  })
}
