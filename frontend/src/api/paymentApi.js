import { apiRequest } from './http'
import { loadGoogleMaps } from './googleMaps'

export const CHECKOUT_RESUME_TOKEN_STORAGE_KEY = 'buyInMinutesCheckoutResumeToken'

function getCheckoutReturnOrigin() {
  return window.location.origin
}

function serializeCartItems(cartItems) {
  return cartItems.map((item) => ({
    id: item.id,
    item_code: item.itemCode || item.id,
    quantity: item.quantity,
    supplier: item.supplier || '',
    supplier_name: item.supplierName || '',
    size: item.size || item.selectedSize || '',
  }))
}

function normalizeDeliveryFeeValue(deliveryFee) {
  const numericValue = Number(deliveryFee)

  return Number.isFinite(numericValue) && numericValue > 0 ? numericValue : 0
}

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

function formatSavedAddress(deliveryAddress) {
  const address = serializeDeliveryAddress(deliveryAddress)

  if (!address || typeof address !== 'object') {
    return ''
  }

  const apartmentLabel = address.label === 'Office' ? 'Office' : 'Apartment'
  const parts = [
    address.label,
    [address.contactName, address.phone].filter(Boolean).join(' - '),
    address.area,
    address.apartmentOfficeName ? `${apartmentLabel} name: ${address.apartmentOfficeName}` : '',
    address.apartmentOfficeNo ? `${apartmentLabel} no: ${address.apartmentOfficeNo}` : '',
    address.building ? `Building/Villa: ${address.building}` : '',
    address.street ? `Street: ${address.street}` : '',
    address.landmark ? `Landmark: ${address.landmark}` : '',
    address.emirate,
  ].filter(Boolean)

  return parts.join(', ')
}

function getLiveCoordinates() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Current location is not supported in this browser.'))
      return
    }

    if (!window.isSecureContext) {
      reject(new Error('Location detection needs a secure (https://) connection.'))
      return
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        })
      },
      (error) => {
        if (error.code === error.PERMISSION_DENIED) {
          reject(new Error('Location access is blocked. Allow location and try again.'))
          return
        }

        if (error.code === error.POSITION_UNAVAILABLE) {
          reject(new Error('Your device could not determine your current location.'))
          return
        }

        if (error.code === error.TIMEOUT) {
          reject(new Error('Detecting your current location took too long.'))
          return
        }

        reject(new Error('Unable to access your current location.'))
      },
      { timeout: 10000 },
    )
  })
}

function buildLocationLabelFromResult(result, coords) {
  const parts = new Map(
    (result?.address_components || []).flatMap((component) =>
      (component.types || []).map((type) => [type, component.long_name]),
    ),
  )
  const route = parts.get('route') || ''
  const locality = parts.get('locality')
    || parts.get('sublocality')
    || parts.get('administrative_area_level_1')
    || ''
  const label = [route, locality].filter(Boolean).join(', ')

  return label || `${coords.lat.toFixed(5)}, ${coords.lng.toFixed(5)}`
}

function formatCoordinates(coords) {
  return `${coords.lat.toFixed(5)}, ${coords.lng.toFixed(5)}`
}

async function getLiveCustomerLocationPayload() {
  const coords = await getLiveCoordinates()
  const coordinateLabel = formatCoordinates(coords)

  try {
    const maps = await loadGoogleMaps()
    const geocoder = new maps.Geocoder()

    const geocodedResult = await new Promise((resolve) => {
      geocoder.geocode({ location: coords }, (results, status) => {
        if (status === 'OK' && results?.length) {
          resolve(results[0])
          return
        }

        resolve(null)
      })
    })

    const resolvedLabel = buildLocationLabelFromResult(geocodedResult, coords)

    if (!resolvedLabel || resolvedLabel === coordinateLabel) {
      return coordinateLabel
    }

    return `${resolvedLabel} (${coordinateLabel})`
  } catch {
    return coordinateLabel
  }
}

export function storeCheckoutResumeToken(checkoutResumeToken) {
  if (!checkoutResumeToken) {
    return
  }

  sessionStorage.setItem(CHECKOUT_RESUME_TOKEN_STORAGE_KEY, checkoutResumeToken)
}

export function clearCheckoutResumeToken() {
  sessionStorage.removeItem(CHECKOUT_RESUME_TOKEN_STORAGE_KEY)
}

let inFlightResume = null

export function resumeCheckoutSession() {
  const checkoutResumeToken = sessionStorage.getItem(CHECKOUT_RESUME_TOKEN_STORAGE_KEY)

  if (!checkoutResumeToken) {
    inFlightResume = null
    return Promise.resolve(null)
  }

  if (inFlightResume && inFlightResume.token === checkoutResumeToken) {
    return inFlightResume.promise
  }

  const promise = (async () => {
    try {
      const response = await apiRequest('/method/buy_in_minutes.payment.resume_checkout_session', {
        method: 'POST',
        body: JSON.stringify({
          checkout_resume_token: checkoutResumeToken,
        }),
      })

      clearCheckoutResumeToken()
      return response
    } catch (error) {
      clearCheckoutResumeToken()
      throw error
    }
  })()

  inFlightResume = { token: checkoutResumeToken, promise }
  return promise
}

export async function createStripeCheckoutSession(
  cartItems,
  salesOrderName = '',
  deliveryAddress = null,
  deliveryDate = '',
  deliverySlot = '',
  deliveryFee = 0,
) {
  const customerLocation = await getLiveCustomerLocationPayload()

  return apiRequest('/method/buy_in_minutes.payment.create_checkout_session', {
    method: 'POST',
    body: JSON.stringify({
      cart_items: serializeCartItems(cartItems),
      sales_order_name: salesOrderName,
      delivery_address: deliveryAddress,
      delivery_date: deliveryDate,
      delivery_slot: deliverySlot,
      customer_location: customerLocation,
      custom_customer_location: customerLocation,
      delivery_fee: normalizeDeliveryFeeValue(deliveryFee),
      return_origin: getCheckoutReturnOrigin(),
    }),
  })
}

export async function createCashOnDeliveryOrder(
  cartItems,
  salesOrderName = '',
  deliveryAddress = null,
  deliveryDate = '',
  deliverySlot = '',
  deliveryFee = 0,
) {
  const customerLocation = await getLiveCustomerLocationPayload()
  const savedAddress = formatSavedAddress(deliveryAddress)
  const serializedDeliveryAddress = serializeDeliveryAddress(deliveryAddress)

  return apiRequest('/method/buy_in_minutes.payment.create_cash_on_delivery_order', {
    method: 'POST',
    body: JSON.stringify({
      cart_items: serializeCartItems(cartItems),
      sales_order_name: salesOrderName,
      delivery_address: serializedDeliveryAddress,
      delivery_date: deliveryDate,
      delivery_slot: deliverySlot,
      custom_delivery_slot: deliverySlot,
      customer_location: customerLocation,
      custom_customer_location: customerLocation,
      address_display: savedAddress,
      delivery_fee: normalizeDeliveryFeeValue(deliveryFee),
    }),
  })
}

export function finalizeStripeCheckout(sessionId) {
  return apiRequest('/method/buy_in_minutes.payment.finalize_stripe_checkout', {
    method: 'POST',
    body: JSON.stringify({
      session_id: sessionId,
    }),
  })
}
