import { apiRequest } from './http'

export const CHECKOUT_RESUME_TOKEN_STORAGE_KEY = 'buyInMinutesCheckoutResumeToken'

function getCheckoutReturnOrigin() {
  return window.location.origin
}

export function storeCheckoutResumeToken(checkoutResumeToken) {
  if (!checkoutResumeToken) {
    return
  }

  sessionStorage.setItem(CHECKOUT_RESUME_TOKEN_STORAGE_KEY, checkoutResumeToken)
}

export function clearCheckoutResumeToken() {
  sessionStorage.removeItem(CHECKOUT_RESUME_TOKEN_STORAGE_KEY)
}

export async function resumeCheckoutSession() {
  const checkoutResumeToken = sessionStorage.getItem(CHECKOUT_RESUME_TOKEN_STORAGE_KEY)

  if (!checkoutResumeToken) {
    return null
  }

  try {
    const response = await apiRequest('/method/buy_in_minutes.payment.resume_checkout_session', {
      method: 'POST',
      body: JSON.stringify({
        checkout_resume_token: checkoutResumeToken,
      }),
    })

    clearCheckoutResumeToken()
    return response
  } catch (error) {
    clearCheckoutResumeToken()
    throw error
  }
}

export function createStripeCheckoutSession(cartItems, salesOrderName = '', deliveryAddress = null) {
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
      delivery_address: deliveryAddress,
      return_origin: getCheckoutReturnOrigin(),
    }),
  })
}

export function createCashOnDeliveryOrder(cartItems, salesOrderName = '', deliveryAddress = null) {
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
      delivery_address: deliveryAddress,
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
