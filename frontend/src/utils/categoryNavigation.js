import { getProducts } from '../api/productApi'
import { saveSelectedProduct } from '../data/productSelectionStore'
import { saveSelectedSupplier } from '../data/supplierSelectionStore'

function normalizeKey(value = '') {
  return String(value)
    .replace(/\s+Shop$/, '')
    .trim()
    .toLowerCase()
}

function getCategoryName(item = {}) {
  return item.itemGroup || item.category || item.name?.replace(/\s+Shop$/, '') || ''
}

function getSelectedBrandProduct(product, item) {
  return {
    ...product,
    sourceListing: {
      type: 'brand',
      label: 'Brand',
      id: item.id || '',
      name: item.name || item.supplier || '',
      supplier: item.supplier || product.supplier || '',
      supplierName: product.supplierName || product.supplier || item.supplier || '',
      storeCode: item.storeCode || '',
      description: item.description || item.supplierDetails || '',
      image: item.image || item.bannerImage || '',
    },
  }
}

function getCategoryKeys(item = {}) {
  return [
    item.itemGroup,
    item.category,
    item.supplier,
    item.storeCode,
    item.id,
    item.name,
    item.name?.replace(/\s+Shop$/, ''),
  ]
    .map(normalizeKey)
    .filter(Boolean)
}

export function getChildCategories(category, categories = []) {
  const parentKeys = new Set(getCategoryKeys(category))

  return categories.filter((candidate) =>
    parentKeys.has(normalizeKey(candidate.parentItemGroup)),
  )
}

export function hasChildCategories(category, categories = []) {
  return getChildCategories(category, categories).length > 0
}

async function loadFirstBrandProduct(item) {
  const queries = []

  if (item.brand) {
    queries.push({ brand: item.brand })
  } else if (item.storeCode || item.id) {
    queries.push({ supplier_store: item.storeCode || item.id })
  }

  if (item.supplier) {
    queries.push({ supplier: item.supplier })
  }

  for (const query of queries) {
    const products = await getProducts({
      ...query,
      limit_page_length: 1,
    })

    if (products.length) {
      return products[0]
    }
  }

  return null
}

export async function openCategoryOrProduct({
  categories = [],
  item,
  router,
  sourceType = 'category',
  onError,
}) {
  const categoryName = getCategoryName(item)

  if (sourceType === 'brand') {
    const product = await loadFirstBrandProduct(item)

    if (!product) {
      onError?.(`No products found in ${item.name}.`)
      return
    }

    const selectedProduct = getSelectedBrandProduct(product, item)
    const supplierName = selectedProduct.supplierName || selectedProduct.supplier || 'Supplier not set'

    saveSelectedProduct(selectedProduct)
    saveSelectedSupplier({
      name: supplierName,
      details: selectedProduct.supplierDetails,
      product: selectedProduct,
    })

    await router.push({
      name: 'product-details',
      params: { productId: selectedProduct.id },
    })
    return
  }

  if (sourceType === 'store') {
    await router.push({
      name: 'store-details',
      params: { categoryName },
    })
    return
  }

  if (hasChildCategories(item, categories)) {
    await router.push({
      name: 'categories',
      query: { category: categoryName },
    })
    return
  }

  if (!categoryName) {
    onError?.(`Unable to open ${item.name}.`)
    return
  }

  await router.push({
    name: 'category-details',
    params: { categoryName },
  })
}
