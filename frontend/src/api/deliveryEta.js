import { customerAddresses } from '../data/addressStore'
import { loadGoogleMaps } from './googleMaps'

const SELECTED_LOCATION_STORAGE_KEY = 'buyInMinutesSelectedLocation'
const CURRENT_LOCATION_COORDS_STORAGE_KEY = 'buyInMinutesCurrentLocationCoords'
const ETA_CACHE = new Map()
const ETA_PROMISE_CACHE = new Map()
const GEOCODE_CACHE = new Map()

const MIN_DELIVERY_MINUTES = 8
const AVERAGE_DELIVERY_SPEED_KMH = 24
const ROAD_DISTANCE_MULTIPLIER = 1.22

export const LOCATION_UPDATED_EVENT = 'buy-in-minutes:location-updated'

function toFiniteNumber(value) {
  const numberValue = Number(value)

  return Number.isFinite(numberValue) ? numberValue : null
}

function normalizeLocationText(value = '') {
  return String(value).trim().replace(/\s+/g, ' ')
}

function getLocationKey(coords) {
  return `${coords.lat.toFixed(5)},${coords.lng.toFixed(5)}`
}

function getStoredSelectedLocation() {
  if (typeof window === 'undefined') {
    return ''
  }

  const selectedLocation = localStorage.getItem(SELECTED_LOCATION_STORAGE_KEY) || ''

  return normalizeLocationText(selectedLocation)
}

function getStoredCurrentLocationCoords() {
  if (typeof window === 'undefined') {
    return null
  }

  try {
    const coords = JSON.parse(localStorage.getItem(CURRENT_LOCATION_COORDS_STORAGE_KEY) || 'null')
    const lat = toFiniteNumber(coords?.lat)
    const lng = toFiniteNumber(coords?.lng)

    if (lat === null || lng === null) {
      return null
    }

    return { lat, lng }
  } catch {
    return null
  }
}

function dispatchLocationUpdated() {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent(LOCATION_UPDATED_EVENT))
  }
}

export function storeCurrentLocationCoords(coords) {
  const lat = toFiniteNumber(coords?.lat)
  const lng = toFiniteNumber(coords?.lng)

  if (typeof window === 'undefined' || lat === null || lng === null) {
    return
  }

  localStorage.setItem(
    CURRENT_LOCATION_COORDS_STORAGE_KEY,
    JSON.stringify({ lat, lng }),
  )
  dispatchLocationUpdated()
}

export function clearCurrentLocationCoords() {
  if (typeof window === 'undefined') {
    return
  }

  localStorage.removeItem(CURRENT_LOCATION_COORDS_STORAGE_KEY)
  dispatchLocationUpdated()
}

function getCustomerLocationSource() {
  const storedCoords = getStoredCurrentLocationCoords()

  if (storedCoords) {
    return {
      key: `current:${getLocationKey(storedCoords)}`,
      coords: storedCoords,
    }
  }

  const defaultAddress = customerAddresses.value.find((address) => address.isDefault)
    || customerAddresses.value[0]

  const latitude = toFiniteNumber(defaultAddress?.latitude)
  const longitude = toFiniteNumber(defaultAddress?.longitude)

  if (latitude !== null && longitude !== null) {
    return {
      key: `address:${defaultAddress?.id || 'default'}:${latitude.toFixed(5)},${longitude.toFixed(5)}`,
      coords: {
        lat: latitude,
        lng: longitude,
      },
    }
  }

  const selectedLocation = getStoredSelectedLocation()

  if (selectedLocation && selectedLocation !== 'Select location') {
    return {
      key: `location:${selectedLocation.toLowerCase()}`,
      address: selectedLocation,
    }
  }

  return {
    key: 'unknown',
    coords: null,
  }
}

async function geocodeLocation(address) {
  const normalizedAddress = normalizeLocationText(address)

  if (!normalizedAddress) {
    return null
  }

  const cacheKey = normalizedAddress.toLowerCase()
  if (GEOCODE_CACHE.has(cacheKey)) {
    return GEOCODE_CACHE.get(cacheKey)
  }

  try {
    const maps = await loadGoogleMaps()
    const geocoder = new maps.Geocoder()
    const result = await new Promise((resolve) => {
      geocoder.geocode(
        { address: normalizedAddress },
        (results, status) => {
          if (status === 'OK' && results?.length && results[0]?.geometry?.location) {
            const location = results[0].geometry.location

            resolve({
              lat: location.lat(),
              lng: location.lng(),
            })
            return
          }

          resolve(null)
        },
      )
    })

    if (result) {
      GEOCODE_CACHE.set(cacheKey, result)
    }

    return result
  } catch {
    return null
  }
}

async function getCustomerCoordinates() {
  const customerLocation = getCustomerLocationSource()

  if (customerLocation.coords) {
    return customerLocation.coords
  }

  if (!customerLocation.address) {
    return null
  }

  return geocodeLocation(customerLocation.address)
}

async function getSupplierCoordinates(supplierAddress) {
  return geocodeLocation(supplierAddress)
}

function getDistanceKm(origin, destination) {
  const earthRadiusKm = 6371
  const latitudeDelta = ((destination.lat - origin.lat) * Math.PI) / 180
  const longitudeDelta = ((destination.lng - origin.lng) * Math.PI) / 180
  const originLatitude = (origin.lat * Math.PI) / 180
  const destinationLatitude = (destination.lat * Math.PI) / 180

  const a =
    Math.sin(latitudeDelta / 2) ** 2
    + Math.cos(originLatitude) * Math.cos(destinationLatitude)
      * Math.sin(longitudeDelta / 2) ** 2

  return 2 * earthRadiusKm * Math.asin(Math.min(1, Math.sqrt(a)))
}

function estimateMinutes(distanceKm) {
  const roadDistanceKm = distanceKm * ROAD_DISTANCE_MULTIPLIER
  const travelMinutes = (roadDistanceKm / AVERAGE_DELIVERY_SPEED_KMH) * 60

  return Math.max(MIN_DELIVERY_MINUTES, Math.round(travelMinutes + 6))
}

export async function getEstimatedDeliveryTimeLabel(product = {}) {
  const supplierAddress = normalizeLocationText(
    product?.supplierDetails?.customGoogleAddress
      || product?.supplierDetails?.custom_google_address
      || product?.supplierAddress
      || '',
  )
  const fallbackDeliveryTime = normalizeLocationText(product?.deliveryTime || '')

  if (!supplierAddress) {
    return fallbackDeliveryTime
  }

  const customerLocation = getCustomerLocationSource()
  const cacheKey = `${supplierAddress.toLowerCase()}::${customerLocation.key}`

  if (ETA_CACHE.has(cacheKey)) {
    return ETA_CACHE.get(cacheKey)
  }

  if (ETA_PROMISE_CACHE.has(cacheKey)) {
    return ETA_PROMISE_CACHE.get(cacheKey)
  }

  const etaPromise = (async () => {
    const [supplierCoords, customerCoords] = await Promise.all([
      getSupplierCoordinates(supplierAddress),
      getCustomerCoordinates(),
    ])

    if (!supplierCoords || !customerCoords) {
      return fallbackDeliveryTime
    }

    const minutes = estimateMinutes(getDistanceKm(supplierCoords, customerCoords))
    return `${minutes} min`
  })()

  ETA_PROMISE_CACHE.set(cacheKey, etaPromise)

  try {
    const etaLabel = await etaPromise
    ETA_CACHE.set(cacheKey, etaLabel)
    return etaLabel
  } finally {
    ETA_PROMISE_CACHE.delete(cacheKey)
  }
}
