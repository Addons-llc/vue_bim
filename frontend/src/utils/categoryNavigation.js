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

function getSourceLabel(item = {}, sourceType = 'category') {
  if (sourceType === 'brand') {
    return 'Brand'
  }

  if (sourceType === 'store' || /\s+Shop$/.test(item.name || '')) {
    return 'Store'
  }

  return 'Category'
}

function getSelectedProductWithSource(product, item, sourceType) {
  return {
    ...product,
    sourceListing: {
      type: sourceType,
      label: getSourceLabel(item, sourceType),
      id: item.id || '',
      name: item.name || getCategoryName(item),
      itemGroup: getCategoryName(item),
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

async function loadFirstProduct(item, sourceType) {
  const categoryName = getCategoryName(item)
  const queries = []

  if (sourceType === 'brand') {
    if (item.storeCode || item.id) {
      queries.push({ supplier_store: item.storeCode || item.id })
    }

    if (item.supplier) {
      queries.push({ supplier: item.supplier })
    }
  }

  if (categoryName) {
    queries.push({ item_group: categoryName })
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

  if (hasChildCategories(item, categories)) {
    await router.push({
      name: 'categories',
      query: { category: categoryName },
    })
    return
  }

  try {
    const product = await loadFirstProduct(item, sourceType)

    if (!product) {
      onError?.(`No products found in ${item.name}.`)
      return
    }

    const selectedProduct = getSelectedProductWithSource(product, item, sourceType)
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
  } catch (error) {
    onError?.(error.message || `Unable to open ${item.name}.`)
  }
}
