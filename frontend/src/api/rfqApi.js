import { apiRequest } from './http'

export async function createRequestForQuotation({ productId, quantity = 1, selectedSize = '' }) {
  const response = await apiRequest('/method/buy_in_minutes.api.create_request_for_quotation', {
    method: 'POST',
    body: JSON.stringify({
      product_id: String(productId || '').trim(),
      quantity: Number(quantity || 1),
      selected_size: String(selectedSize || '').trim(),
    }),
  })

  return response?.message || null
}

export async function createRequestForQuotationFromCart(cartItems = []) {
  const quotationRequests = []

  for (const item of cartItems) {
    const rfq = await createRequestForQuotation({
      productId: item.itemCode || item.id,
      quantity: Number(item.quantity || 1),
      selectedSize: item.size || item.selectedSize || '',
    })

    if (rfq) {
      quotationRequests.push(rfq)
    }
  }

  return quotationRequests
}
