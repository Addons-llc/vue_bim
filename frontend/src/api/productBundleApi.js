import { PRODUCT_BUNDLE_API_PATH } from './config'
import { apiRequest } from './http'
import { getImageUrl, mapItemToProduct } from './itemApi'

function toNumber(value) {
  const numberValue = Number(value)

  return Number.isFinite(numberValue) ? numberValue : 0
}

function mapBundleComponent(component = {}) {
  return {
    itemCode: component.item_code,
    name: component.item_name || component.item_code,
    image: getImageUrl(component.image),
    qty: toNumber(component.qty),
    uom: component.uom || '',
    unitPrice: toNumber(component.unit_price),
  }
}

async function mapProductBundle(item) {
  const product = await mapItemToProduct(item)
  const bundleItems = (item.bundle_items || []).map(mapBundleComponent)
  const bundleItemsValue = toNumber(item.bundle_items_value)

  return {
    ...product,
    description: product.description || item.bundle_description || '',
    isBundle: true,
    productBundle: item.product_bundle,
    bundleItems,
    bundleItemsValue,
    // Show the combined price of the contents as the "was" price only when the kit is actually cheaper.
    oldPrice: bundleItemsValue > product.price ? bundleItemsValue : null,
  }
}

export async function getProductBundles(params = {}) {
  const query = new URLSearchParams({
    limit_page_length: params.limit_page_length || 12,
    published: 1,
  })

  if (params.item_group) {
    query.set('item_group', params.item_group)
  }

  const response = await apiRequest(`${PRODUCT_BUNDLE_API_PATH}?${query.toString()}`)
  const bundles = response.message || []

  return Promise.all(bundles.map(mapProductBundle))
}
