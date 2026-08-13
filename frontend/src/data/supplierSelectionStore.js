const SELECTED_SUPPLIER_STORAGE_KEY = 'buyInMinutesSelectedSupplier'

function dedupeProducts(products = []) {
  return Array.from(
    products.reduce((productMap, product) => {
      if (product?.id) {
        productMap.set(product.id, product)
      }

      return productMap
    }, new Map()).values(),
  )
}

export function saveSelectedSupplier(supplier) {
  if (!supplier?.name) {
    return
  }

  const existingSupplier = getSelectedSupplier(supplier.name)
  const products = dedupeProducts([
    ...(existingSupplier?.products || []),
    ...(supplier.products || []),
    supplier.product,
  ])

  sessionStorage.setItem(
    SELECTED_SUPPLIER_STORAGE_KEY,
    JSON.stringify({
      ...existingSupplier,
      ...supplier,
      details: supplier.details || existingSupplier?.details || supplier.product?.supplierDetails,
      product: supplier.product || existingSupplier?.product || products[0],
      products,
    }),
  )
}

export function getSelectedSupplier(supplierName) {
  try {
    const supplier = JSON.parse(sessionStorage.getItem(SELECTED_SUPPLIER_STORAGE_KEY))

    return supplier?.name === supplierName ? supplier : null
  } catch {
    return null
  }
}
