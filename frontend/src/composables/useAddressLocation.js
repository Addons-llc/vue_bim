import { ref } from 'vue'
import { loadGoogleMaps } from '../api/googleMaps'

const UAE_COUNTRY_CODE = 'AE'
const UNWANTED_RESULT_TYPES = ['parking', 'point_of_interest', 'establishment']

let addressGeocoder
let addressPlaceApi

function isParkingLabel(label = '') {
  return /parking/i.test(label)
}

function isPlusCodeLabel(label = '') {
  return /^[23456789CFGHJMPQRVWX]{4,}\+[23456789CFGHJMPQRVWX]{2,}/i.test(label.trim())
}

function normalizeDisplayedLocation(location = '') {
  return location.replace(
    /^[23456789CFGHJMPQRVWX]{4,}\+[23456789CFGHJMPQRVWX]{2,}\s*-\s*/i,
    '',
  )
}

function getAddressComponent(result = {}, type) {
  const component = (result.address_components || []).find((item) =>
    (item.types || []).includes(type),
  )

  return component?.long_name || ''
}

function getAddressComponentValues(result = {}, types = []) {
  return types
    .map((type) => getAddressComponent(result, type))
    .filter(Boolean)
}

function getAddressComponentCandidates(result = {}, types = []) {
  return (result.address_components || [])
    .flatMap((component) => (
      (component.types || []).some((type) => types.includes(type))
        ? [component.long_name || '']
        : []
    ))
    .filter(Boolean)
}

function pickMostSpecificAddressValue(values = []) {
  return [...new Set(values.filter(Boolean))].sort((left, right) => {
    const leftScore = [/\d/.test(left), left.length]
    const rightScore = [/\d/.test(right), right.length]

    if (leftScore[0] !== rightScore[0]) {
      return Number(rightScore[0]) - Number(leftScore[0])
    }

    return rightScore[1] - leftScore[1]
  })[0] || ''
}

function isUnitedArabEmiratesPlace(result = {}) {
  return (result.address_components || []).some((component) => (
    (component.types || []).includes('country')
    && component.short_name === UAE_COUNTRY_CODE
  ))
}

function isUnwantedLocationResult(result = {}) {
  const types = result.types || []
  const formattedAddress = result.formatted_address || ''

  return (
    isPlusCodeLabel(formattedAddress)
    || isParkingLabel(formattedAddress)
    || UNWANTED_RESULT_TYPES.some((type) => types.includes(type))
  )
}

function pickPreferredAddressResult(results = []) {
  return (
    results.find((result) => {
      const types = result.types || []

      return !isUnwantedLocationResult(result) && ['premise', 'subpremise'].some((type) => types.includes(type))
    })
    || results.find((result) => {
      const types = result.types || []

      return !isUnwantedLocationResult(result) && ['street_address', 'route'].some((type) => types.includes(type))
    })
    || results.find((result) => {
      const types = result.types || []

      return (
        !isUnwantedLocationResult(result)
        && ['neighborhood', 'sublocality', 'sublocality_level_1', 'locality'].some((type) => types.includes(type))
      )
    })
    || results.find((result) => !isUnwantedLocationResult(result))
    || results[0]
  )
}

function buildAddressFieldsFromPlace(place = {}) {
  const streetNumber = getAddressComponent(place, 'street_number')
  const routeName = getAddressComponent(place, 'route')
  const streetAddress = [streetNumber, routeName].filter(Boolean).join(' ')
  const premise = getAddressComponent(place, 'premise')
  const subpremise = getAddressComponent(place, 'subpremise')
  const emirate = getAddressComponent(place, 'administrative_area_level_1')
  const area = pickMostSpecificAddressValue([
    ...getAddressComponentCandidates(place, [
      'neighborhood',
      'sublocality_level_2',
      'sublocality_level_1',
      'sublocality',
    ]),
    ...getAddressComponentValues(place, [
      'locality',
      'administrative_area_level_2',
    ]),
  ]) || ''
  const placeName = place.name && !isParkingLabel(place.name) && !isPlusCodeLabel(place.name)
    ? place.name
    : ''
  const formattedAddress = normalizeDisplayedLocation(place.formatted_address || '')
  const formattedAddressLead = formattedAddress.split(',').map((part) => part.trim()).find((part) => (
    part
    && part !== area
    && !isPlusCodeLabel(part)
    && !isParkingLabel(part)
  )) || ''
  const building = [
    [subpremise, premise].filter(Boolean).join(', '),
    premise,
    subpremise,
    streetAddress,
    placeName,
    formattedAddressLead,
    routeName,
  ].find((value) => (
    value
    && value !== area
    && !isPlusCodeLabel(value)
    && !isParkingLabel(value)
  )) || ''

  return {
    area,
    building,
    street: streetAddress || routeName,
    emirate,
    landmark: [placeName, routeName, formattedAddressLead, formattedAddress].find((value) => (
      value
      && value !== area
      && value !== building
      && !isPlusCodeLabel(value)
      && !isParkingLabel(value)
    )) || '',
  }
}

function isStreetOnlyBuilding(building = '', place = {}) {
  const routeName = getAddressComponent(place, 'route')

  return Boolean(building && routeName && building === routeName)
}

function pickNearbyBuildingPlace(places = []) {
  return places.find((place) => {
    const name = place.name || ''
    const types = place.types || []

    return (
      name
      && !isPlusCodeLabel(name)
      && !isParkingLabel(name)
      && !UNWANTED_RESULT_TYPES.some((type) => types.includes(type))
    )
  }) || null
}

function pickNearbyLandmarkPlace(places = [], excludedValues = []) {
  return places.find((place) => {
    const name = place.name || ''
    const types = place.types || []

    return (
      name
      && !excludedValues.includes(name)
      && !isPlusCodeLabel(name)
      && !isParkingLabel(name)
      && !types.includes('parking')
    )
  }) || null
}

function getPlaceAddressComponents(place = {}) {
  return (place.addressComponents || []).map((component) => ({
    long_name: component.longText || component.long_name || '',
    short_name: component.shortText || component.short_name || '',
    types: component.types || [],
  }))
}

async function getAddressPlaceDetails(placeId) {
  if (!addressPlaceApi?.Place || !placeId) {
    return null
  }

  try {
    const place = new addressPlaceApi.Place({ id: placeId })

    await place.fetchFields({
      fields: ['displayName', 'formattedAddress', 'addressComponents', 'location', 'types'],
    })

    return {
      name: place.displayName,
      formatted_address: place.formattedAddress,
      address_components: getPlaceAddressComponents(place),
      geometry: place.location ? { location: place.location } : undefined,
      types: place.types || [],
    }
  } catch {
    return null
  }
}

async function getNearbyBuildingPlace(location) {
  if (!addressPlaceApi?.Place || !location) {
    return null
  }

  try {
    const { places = [] } = await addressPlaceApi.Place.searchNearby({
      fields: ['displayName', 'formattedAddress', 'location', 'types'],
      locationRestriction: {
        center: location,
        radius: 80,
      },
      rankPreference: addressPlaceApi.SearchNearbyRankPreference.DISTANCE,
    })
    const normalizedPlaces = places.map((place) => ({
      name: place.displayName,
      formatted_address: place.formattedAddress,
      location: place.location,
      types: place.types || [],
    }))

    return pickNearbyBuildingPlace(normalizedPlaces)
  } catch {
    return null
  }
}

function searchNearbyPlacesWithService(location) {
  return new Promise((resolve) => {
    if (!window.google?.maps?.places?.PlacesService || !location) {
      resolve([])
      return
    }

    const placesService = new window.google.maps.places.PlacesService(document.createElement('div'))

    placesService.nearbySearch(
      {
        location,
        radius: 80,
      },
      (results, status) => {
        if (status !== window.google.maps.places.PlacesServiceStatus.OK || !results) {
          resolve([])
          return
        }

        resolve(results.map((place) => ({
          name: place.name,
          formatted_address: place.vicinity,
          location: place.geometry?.location,
          types: place.types || [],
        })))
      },
    )
  })
}

async function getNearbyAddressPlaces(location) {
  const places = []
  const newPlacesResult = await getNearbyBuildingPlace(location)

  if (newPlacesResult) {
    places.push(newPlacesResult)
  }

  const servicePlaces = await searchNearbyPlacesWithService(location)

  return [...places, ...servicePlaces]
}

function describeAddressGeolocationError(error) {
  if (error.code === error.PERMISSION_DENIED) {
    return 'Location access is blocked. Allow location for this site in your browser and device settings, then try again.'
  }

  if (error.code === error.POSITION_UNAVAILABLE) {
    return 'Your device could not determine your location. Check that location services are turned on.'
  }

  if (error.code === error.TIMEOUT) {
    return 'Detecting your location took too long. Please try again.'
  }

  return 'Unable to access your current location.'
}

async function initializeAddressLocationServices(addressLocationError) {
  if (addressGeocoder && addressPlaceApi) {
    return true
  }

  try {
    const maps = await loadGoogleMaps()
    addressGeocoder = new maps.Geocoder()
    addressPlaceApi = await window.google.maps.importLibrary('places')
    return true
  } catch (error) {
    addressLocationError.value = error.message || 'Unable to load location services.'
    return false
  }
}

export function useAddressLocation() {
  const isDetectingAddressLocation = ref(false)
  const addressLocationError = ref('')

  async function fillAddressFromCurrentLocation(addressForm) {
    addressLocationError.value = ''

    if (!navigator.geolocation) {
      addressLocationError.value = 'Current location is not supported in this browser.'
      return
    }

    if (!window.isSecureContext) {
      addressLocationError.value = 'Location detection needs a secure (https://) connection. It will work once this site is served over https.'
      return
    }

    const servicesReady = await initializeAddressLocationServices(addressLocationError)

    if (!servicesReady) {
      return
    }

    isDetectingAddressLocation.value = true

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const currentPosition = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        }

        addressGeocoder.geocode({ location: currentPosition }, async (results, status) => {
          try {
            const geocodedResult = status === 'OK' ? pickPreferredAddressResult(results) : null
            const placeDetails = geocodedResult?.place_id
              ? await getAddressPlaceDetails(geocodedResult.place_id)
              : null
            const preferredPlace = placeDetails || geocodedResult

            if (!preferredPlace) {
              addressLocationError.value = 'Unable to resolve your exact address.'
              return
            }

            if (!isUnitedArabEmiratesPlace(preferredPlace)) {
              addressLocationError.value = 'Please use a location in the United Arab Emirates.'
              return
            }

            const detectedFields = buildAddressFieldsFromPlace(preferredPlace)
            const nearbyPlaces = await getNearbyAddressPlaces(currentPosition)
            const nearbyBuildingPlace = !detectedFields.building || isStreetOnlyBuilding(detectedFields.building, preferredPlace)
              ? pickNearbyBuildingPlace(nearbyPlaces)
              : null
            const nearbyBuildingName = nearbyBuildingPlace?.name && !isParkingLabel(nearbyBuildingPlace.name)
              ? nearbyBuildingPlace.name
              : ''
            const finalBuilding = nearbyBuildingName || detectedFields.building || addressForm.value.building
            const nearbyLandmark = pickNearbyLandmarkPlace(nearbyPlaces, [
              finalBuilding,
              detectedFields.area,
              detectedFields.landmark,
            ])
            const nearbyLandmarkName = nearbyLandmark?.name && !isParkingLabel(nearbyLandmark.name)
              ? nearbyLandmark.name
              : ''

            addressForm.value = {
              ...addressForm.value,
              area: detectedFields.area || addressForm.value.area,
              building: finalBuilding,
              street: detectedFields.street || addressForm.value.street,
              landmark: nearbyLandmarkName || detectedFields.landmark || addressForm.value.landmark,
              emirate: detectedFields.emirate || addressForm.value.emirate,
              latitude: String(currentPosition.lat),
              longitude: String(currentPosition.lng),
            }
          } catch (error) {
            addressLocationError.value = error.message || 'Unable to resolve your exact address.'
          } finally {
            isDetectingAddressLocation.value = false
          }
        })
      },
      (error) => {
        addressLocationError.value = describeAddressGeolocationError(error)
        isDetectingAddressLocation.value = false
      },
      {
        timeout: 10000,
      },
    )
  }

  return {
    addressLocationError,
    fillAddressFromCurrentLocation,
    isDetectingAddressLocation,
  }
}
