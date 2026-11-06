/**
 * Route to a product's page. URLs use the readable slug (/products/amul-butter-500g) and
 * fall back to the item code; the backend resolves either.
 */
export function productRoute(product) {
  return {
    name: 'product-details',
    params: { productId: product?.slug || product?.id || '' },
  }
}

/** True when `key` (a URL param) points at this product, by slug or item code. */
export function isProductKey(product, key) {
  return Boolean(product && key && (product.slug === key || product.id === key))
}
