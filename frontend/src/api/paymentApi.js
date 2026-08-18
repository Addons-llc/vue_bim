import { apiRequest } from './http'

export const CHECKOUT_RESUME_TOKEN_STORAGE_KEY = 'buyInMinutesCheckoutResumeToken'

function getCheckoutReturnOrigin() {
  return window.location.origin
}

function serializeCartItems(cartItems) {
  return cartItems.map((item) => ({
    id: item.id,
    item_code: item.itemCode || item.id,
    quantity: item.quantity,
    supplier: item.supplier || '',
    supplier_name: item.supplierName || '',
    size: item.size || item.selectedSize || '',
  }))
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

let inFlightResume = null

export function resumeCheckoutSession() {
  const checkoutResumeToken = sessionStorage.getItem(CHECKOUT_RESUME_TOKEN_STORAGE_KEY)

  if (!checkoutResumeToken) {
    inFlightResume = null
    return Promise.resolve(null)
  }

  if (inFlightResume && inFlightResume.token === checkoutResumeToken) {
    return inFlightResume.promise
  }

  const promise = (async () => {
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
  })()

  inFlightResume = { token: checkoutResumeToken, promise }
  return promise
}

export function createStripeCheckoutSession(
  cartItems,
  salesOrderName = '',
  deliveryAddress = null,
  deliveryDate = '',
  deliverySlot = '',
) {
  return apiRequest('/method/buy_in_minutes.payment.create_checkout_session', {
    method: 'POST',
    body: JSON.stringify({
      cart_items: serializeCartItems(cartItems),
      sales_order_name: salesOrderName,
      delivery_address: deliveryAddress,
      delivery_date: deliveryDate,
      delivery_slot: deliverySlot,
      return_origin: getCheckoutReturnOrigin(),
    }),
  })
}

export function createCashOnDeliveryOrder(
  cartItems,
  salesOrderName = '',
  deliveryAddress = null,
  deliveryDate = '',
  deliverySlot = '',
) {
  return apiRequest('/method/buy_in_minutes.payment.create_cash_on_delivery_order', {
    method: 'POST',
    body: JSON.stringify({
      cart_items: serializeCartItems(cartItems),
      sales_order_name: salesOrderName,
      delivery_address: deliveryAddress,
      delivery_date: deliveryDate,
      delivery_slot: deliverySlot,
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
