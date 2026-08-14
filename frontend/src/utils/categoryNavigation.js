function normalizeKey(value = '') {
  return String(value)
    .replace(/\s+Shop$/, '')
    .trim()
    .toLowerCase()
}

function getCategoryName(item = {}) {
  return item.itemGroup || item.category || item.name?.replace(/\s+Shop$/, '') || ''
}

function getStoreIdentifier(item = {}) {
  return item.storeCode || item.id || item.name || ''
}

function getBrandIdentifier(item = {}) {
  return item.brand || item.id || item.name || ''
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

export async function openCategoryOrProduct({
  categories = [],
  item,
  router,
  sourceType = 'category',
  onError,
}) {
  const categoryName = getCategoryName(item)

  if (sourceType === 'brand') {
    const brandIdentifier = getBrandIdentifier(item)

    if (!brandIdentifier) {
      onError?.(`Unable to open ${item.name}.`)
      return
    }

    await router.push({
      name: 'brand-details',
      params: { brandName: brandIdentifier },
    })
    return
  }

  if (sourceType === 'store') {
    const storeIdentifier = getStoreIdentifier(item)

    if (!storeIdentifier) {
      onError?.(`Unable to open ${item.name}.`)
      return
    }

    await router.push({
      name: 'store-details',
      params: { categoryName: storeIdentifier },
      query: item.name ? { title: item.name } : undefined,
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
