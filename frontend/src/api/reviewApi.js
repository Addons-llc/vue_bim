import { apiRequest } from './http'

function normalizeReview(review = {}) {
  const rating = Number(review.rating)

  return {
    id: String(review.id || ''),
    customerName: String(review.customerName || review.customer_name || 'Anonymous'),
    rating: Number.isFinite(rating) ? Math.max(0, Math.min(5, Math.round(rating))) : 0,
    description: String(review.description || ''),
  }
}

export async function getProductReviews(productId, supplier = '') {
  const normalizedProductId = String(productId || '').trim()
  const normalizedSupplier = String(supplier || '').trim()

  if (!normalizedProductId && !normalizedSupplier) {
    return []
  }

  const query = new URLSearchParams()
  if (normalizedProductId) {
    query.set('product_id', normalizedProductId)
  }
  if (normalizedSupplier) {
    query.set('supplier', normalizedSupplier)
  }

  const response = await apiRequest(
    `/method/buy_in_minutes.api.get_product_reviews?${query.toString()}`,
  )

  return Array.isArray(response.message)
    ? response.message.map(normalizeReview)
    : []
}

export async function addProductReview({ orderName, productId, rating, description }) {
  const response = await apiRequest('/method/buy_in_minutes.api.add_product_review', {
    method: 'POST',
    body: JSON.stringify({
      order_name: String(orderName || '').trim(),
      product_id: String(productId || '').trim(),
      rating: Number(rating || 0),
      description: String(description || '').trim(),
    }),
  })

  return normalizeReview(response?.message || {})
}
