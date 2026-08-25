import { customerAddresses } from '../data/addressStore'
import { loadGoogleMaps } from './googleMaps'

const SELECTED_LOCATION_STORAGE_KEY = 'buyInMinutesSelectedLocation'
const CURRENT_LOCATION_COORDS_STORAGE_KEY = 'buyInMinutesCurrentLocationCoords'
const UAE_COUNTRY_CODE = 'AE'
const ETA_CACHE = new Map()
const ETA_PROMISE_CACHE = new Map()
const GEOCODE_CACHE = new Map()
const ROUTE_METRICS_CACHE = new Map()

export const LOCATION_UPDATED_EVENT = 'buy-in-minutes:location-updated'

function toFiniteNumber(value) {
  const numberValue = Number(value)

  return Number.isFinite(numberValue) ? numberValue : null
}

function normalizeLocationText(value = '') {
  return String(value).trim().replace(/\s+/g, ' ')
}

function getCoordinatePair(latitudeValue, longitudeValue) {
  const latitude = toFiniteNumber(latitudeValue)
  const longitude = toFiniteNumber(longitudeValue)

  if (latitude === null || longitude === null) {
    return null
  }

  return {
    lat: latitude,
    lng: longitude,
  }
}

function isUnitedArabEmiratesResult(result = {}) {
  return (result.address_components || []).some((component) => (
    (component.types || []).includes('country')
    && String(component.short_name || '').toUpperCase() === UAE_COUNTRY_CODE
  ))
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
    const uaeBounds = new maps.LatLngBounds(
      new maps.LatLng(22.5, 51.4),
      new maps.LatLng(26.5, 56.8),
    )
    const result = await new Promise((resolve) => {
      geocoder.geocode(
        {
          address: normalizedAddress,
          bounds: uaeBounds,
          componentRestrictions: { country: UAE_COUNTRY_CODE },
          region: UAE_COUNTRY_CODE,
        },
        (results, status) => {
          if (status === 'OK' && results?.length) {
            const preferredResult = results.find(isUnitedArabEmiratesResult) || results[0]
            if (!preferredResult?.geometry?.location || !isUnitedArabEmiratesResult(preferredResult)) {
              resolve(null)
              return
            }
            const location = preferredResult.geometry.location

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

  return null
}

async function getSupplierCoordinates(product = {}) {
  const supplierCoords = getCoordinatePair(
    product?.supplierDetails?.customLatitude
      || product?.supplierDetails?.custom_latitude
      || product?.supplierLatitude
      || product?.custom_latitude,
    product?.supplierDetails?.customLongitude
      || product?.supplierDetails?.custom_longitude
      || product?.supplierLongitude
      || product?.custom_longitude,
  )

  if (supplierCoords) {
    return supplierCoords
  }

  const supplierAddress = normalizeLocationText(
    product?.supplierDetails?.customGoogleAddress
      || product?.supplierDetails?.custom_google_address
      || product?.supplierAddress
      || '',
  )

  if (!supplierAddress) {
    return null
  }

  return geocodeLocation(supplierAddress)
}

async function getRouteMetrics(origin, destination) {
  if (!origin || !destination) {
    return null
  }

  const cacheKey = `${getLocationKey(origin)}::${getLocationKey(destination)}`
  if (ROUTE_METRICS_CACHE.has(cacheKey)) {
    return ROUTE_METRICS_CACHE.get(cacheKey)
  }

  try {
    const maps = await loadGoogleMaps()
    const directionsService = new maps.DirectionsService()
    const route = await new Promise((resolve, reject) => {
      directionsService.route(
        {
          origin,
          destination,
          travelMode: maps.TravelMode.DRIVING,
          drivingOptions: {
            departureTime: new Date(),
          },
          provideRouteAlternatives: false,
        },
        (result, status) => {
          if (status === 'OK' && result?.routes?.length) {
            resolve(result)
            return
          }

          reject(new Error(status || 'DIRECTIONS_FAILED'))
        },
      )
    })

    const legs = route.routes.flatMap((candidateRoute) => candidateRoute.legs || [])
    const durationSeconds = legs
      .reduce((total, leg) => (
        total + Number(
          leg.duration_in_traffic?.value
          ?? leg.duration?.value
          ?? 0
        )
      ), 0)
    const distanceMeters = legs
      .reduce((total, leg) => (
        total + Number(leg.distance?.value ?? 0)
      ), 0)

    if (!durationSeconds && !distanceMeters) {
      return null
    }

    const metrics = {
      durationMinutes: durationSeconds ? Math.max(1, Math.round(durationSeconds / 60)) : null,
      distanceKm: distanceMeters ? distanceMeters / 1000 : null,
    }

    ROUTE_METRICS_CACHE.set(cacheKey, metrics)
    return metrics
  } catch {
    return null
  }
}

async function getRouteDurationMinutes(origin, destination) {
  const metrics = await getRouteMetrics(origin, destination)

  return metrics?.durationMinutes || null
}

export async function getCustomerToSupplierDistanceKm(product = {}) {
  const [supplierCoords, customerCoords] = await Promise.all([
    getSupplierCoordinates(product),
    getCustomerCoordinates(),
  ])

  if (!supplierCoords || !customerCoords) {
    return null
  }

  const metrics = await getRouteMetrics(supplierCoords, customerCoords)

  return metrics?.distanceKm || null
}

export async function getEstimatedDeliveryTimeLabel(product = {}) {
  const fallbackDeliveryTime = normalizeLocationText(product?.deliveryTime || '')

  const customerLocation = getCustomerLocationSource()
  const supplierCoordinateKey = [
    product?.supplierDetails?.customLatitude
      || product?.supplierDetails?.custom_latitude
      || product?.supplierLatitude
      || product?.custom_latitude
      || '',
    product?.supplierDetails?.customLongitude
      || product?.supplierDetails?.custom_longitude
      || product?.supplierLongitude
      || product?.custom_longitude
      || '',
  ].join(',')
  const supplierAddressKey = normalizeLocationText(
    product?.supplierDetails?.customGoogleAddress
      || product?.supplierDetails?.custom_google_address
      || product?.supplierAddress
      || '',
  ).toLowerCase()
  const supplierKey = supplierCoordinateKey !== ','
    ? `coords:${supplierCoordinateKey}`
    : `address:${supplierAddressKey}`

  if (supplierKey === 'address:' && !supplierAddressKey) {
    return fallbackDeliveryTime
  }

  const cacheKey = `${supplierKey}::${customerLocation.key}`

  if (ETA_CACHE.has(cacheKey)) {
    return ETA_CACHE.get(cacheKey)
  }

  if (ETA_PROMISE_CACHE.has(cacheKey)) {
    return ETA_PROMISE_CACHE.get(cacheKey)
  }

  const etaPromise = (async () => {
    const [supplierCoords, customerCoords] = await Promise.all([
      getSupplierCoordinates(product),
      getCustomerCoordinates(),
    ])

    if (!supplierCoords || !customerCoords) {
      return fallbackDeliveryTime
    }

    const minutes = await getRouteDurationMinutes(supplierCoords, customerCoords)

    if (!minutes) {
      return fallbackDeliveryTime
    }

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
