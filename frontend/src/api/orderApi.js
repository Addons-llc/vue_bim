import { apiRequest } from './http'

const SELECTED_LOCATION_STORAGE_KEY = 'buyInMinutesSelectedLocation'
const CURRENT_LOCATION_COORDS_STORAGE_KEY = 'buyInMinutesCurrentLocationCoords'

function getCustomerLocationPayload() {
  const selectedLocation = (localStorage.getItem(SELECTED_LOCATION_STORAGE_KEY) || '').trim()

  try {
    const currentCoords = JSON.parse(localStorage.getItem(CURRENT_LOCATION_COORDS_STORAGE_KEY) || 'null')
    const lat = Number(currentCoords?.lat)
    const lng = Number(currentCoords?.lng)

    if (Number.isFinite(lat) && Number.isFinite(lng)) {
      return selectedLocation
        ? `${selectedLocation} (${lat.toFixed(5)}, ${lng.toFixed(5)})`
        : `${lat.toFixed(5)}, ${lng.toFixed(5)}`
    }
  } catch {
    // Ignore malformed stored coordinates and fall back to the selected location label.
  }

  return selectedLocation
}

function getSalesOrderCustomerLocationPayload() {
  const customerLocation = getCustomerLocationPayload()

  return {
    customer_location: customerLocation,
    custom_customer_location: customerLocation,
  }
}

export function syncCartSalesOrder(
  cartItems,
  salesOrderName = '',
  deliveryAddress = null,
  deliveryDate = '',
  deliverySlot = '',
) {
  return apiRequest('/method/buy_in_minutes.payment.sync_cart_sales_order', {
    method: 'POST',
    body: JSON.stringify({
      cart_items: cartItems.map((item) => ({
        id: item.id,
        item_code: item.itemCode || item.id,
        quantity: item.quantity,
      })),
      sales_order_name: salesOrderName,
      delivery_address: deliveryAddress,
      delivery_date: deliveryDate,
      delivery_slot: deliverySlot,
      ...getSalesOrderCustomerLocationPayload(),
    }),
  })
}

export function getOrders() {
  return apiRequest('/orders')
}

export function getOrderById(orderId) {
  return apiRequest(`/orders/${orderId}`)
}

export function getSalesOrder(salesOrderName) {
  const query = new URLSearchParams({
    sales_order_name: salesOrderName,
  })

  return apiRequest(`/method/buy_in_minutes.api.get_sales_order?${query.toString()}`)
}

export function getOrderedProducts() {
  return apiRequest('/method/buy_in_minutes.api.get_ordered_products')
}

export function createOrder(orderData) {
  return apiRequest('/orders', {
    method: 'POST',
    body: JSON.stringify(orderData),
  })
}
