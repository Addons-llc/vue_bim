const SELECTED_PRODUCT_STORAGE_KEY = 'buyInMinutesSelectedProduct'

export function saveSelectedProduct(product) {
  if (!product?.id) {
    return
  }

  sessionStorage.setItem(SELECTED_PRODUCT_STORAGE_KEY, JSON.stringify(product))
}

export function getSelectedProduct(productId) {
  try {
    const product = JSON.parse(sessionStorage.getItem(SELECTED_PRODUCT_STORAGE_KEY))

    return product?.id === productId ? product : null
  } catch {
    return null
  }
}
