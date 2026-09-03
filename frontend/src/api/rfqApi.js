import { apiRequest } from './http'

function normalizeAddressValue(value) {
  return String(value || '').trim()
}

function serializeDeliveryAddress(deliveryAddress) {
  if (!deliveryAddress || typeof deliveryAddress !== 'object') {
    return deliveryAddress || null
  }

  const normalizedAddress = {
    id: normalizeAddressValue(deliveryAddress.id),
    label: normalizeAddressValue(deliveryAddress.label),
    contactName: normalizeAddressValue(deliveryAddress.contactName),
    phone: normalizeAddressValue(deliveryAddress.phone),
    email: normalizeAddressValue(deliveryAddress.email),
    area: normalizeAddressValue(deliveryAddress.area),
    apartmentOfficeName: normalizeAddressValue(deliveryAddress.apartmentOfficeName),
    apartmentOfficeNo: normalizeAddressValue(deliveryAddress.apartmentOfficeNo),
    building: normalizeAddressValue(deliveryAddress.building),
    street: normalizeAddressValue(deliveryAddress.street),
    landmark: normalizeAddressValue(deliveryAddress.landmark),
    emirate: normalizeAddressValue(deliveryAddress.emirate),
    latitude: normalizeAddressValue(deliveryAddress.latitude),
    longitude: normalizeAddressValue(deliveryAddress.longitude),
    isDefault: Boolean(deliveryAddress.isDefault),
  }

  return {
    ...normalizedAddress,
    contact_name: normalizedAddress.contactName,
    apartment_office_name: normalizedAddress.apartmentOfficeName,
    apartment_office_no: normalizedAddress.apartmentOfficeNo,
  }
}

export async function createRequestForQuotation({
  productId,
  quantity = 1,
  selectedSize = '',
  deliveryAddress = null,
  requiredDate = '',
  email = '',
  submitRequest = false,
} = {}) {
  const response = await apiRequest('/method/buy_in_minutes.api.create_request_for_quotation', {
    method: 'POST',
    body: JSON.stringify({
      product_id: String(productId || '').trim(),
      quantity: Number(quantity || 1),
      selected_size: String(selectedSize || '').trim(),
      delivery_address: serializeDeliveryAddress(deliveryAddress),
      required_date: String(requiredDate || '').trim(),
      email: String(email || '').trim(),
      submit_request: Boolean(submitRequest),
    }),
  })

  return response?.message || null
}

export async function createRequestForQuotationFromCart(
  cartItems = [],
  deliveryAddress = null,
  requiredDate = '',
  email = '',
) {
  const response = await apiRequest('/method/buy_in_minutes.api.create_request_for_quotation_from_cart', {
    method: 'POST',
    body: JSON.stringify({
      cart_items: cartItems.map((item) => ({
        id: item.id,
        item_code: item.itemCode || item.id,
        quantity: Number(item.quantity || 1),
        supplier: item.supplier || '',
        supplier_name: item.supplierName || '',
        size: item.size || item.selectedSize || '',
      })),
      delivery_address: serializeDeliveryAddress(deliveryAddress),
      required_date: String(requiredDate || '').trim(),
      email: String(email || '').trim(),
      submit_request: true,
    }),
  })

  return response?.message || null
}
