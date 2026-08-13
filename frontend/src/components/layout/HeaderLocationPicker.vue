<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { loadGoogleMaps } from '../../api/googleMaps'

const route = useRoute()
const selectedLocation = ref('Select location')
const isLocationDialogOpen = ref(false)
const isDetectingLocation = ref(false)
const locationError = ref('')
const locationSearchText = ref('')
const locationSuggestions = ref([])

const LOCATION_STORAGE_KEY = 'buyInMinutesSelectedLocation'
const AUTO_PROMPT_LOCATION_KEY = 'buyInMinutesPromptLocationOnHome'
const UNWANTED_RESULT_TYPES = ['parking', 'point_of_interest', 'establishment', 'premise', 'subpremise']

let autocompleteService
let geocoder
let placesSessionToken
let placesService
let hasAttemptedAutoLocation = false

function setSelectedLocation(location) {
  selectedLocation.value = location

  if (location) {
    localStorage.setItem(LOCATION_STORAGE_KEY, location)
  } else {
    localStorage.removeItem(LOCATION_STORAGE_KEY)
  }
}

function isPlusCodeLabel(label = '') {
  return /^[23456789CFGHJMPQRVWX]{4,}\+[23456789CFGHJMPQRVWX]{2,}/i.test(label.trim())
}

function isParkingLabel(label = '') {
  return /parking/i.test(label)
}

function normalizeDisplayedLocation(location = '') {
  return location.replace(
    /^[23456789CFGHJMPQRVWX]{4,}\+[23456789CFGHJMPQRVWX]{2,}\s*-\s*/i,
    '',
  )
}

function buildReadableLocationFromComponents(result = {}) {
  const componentValues = new Map(
    (result.address_components || []).flatMap((component) =>
      (component.types || []).map((type) => [type, component.long_name]),
    ),
  )

  const getClean = (type) => {
    const value = componentValues.get(type)
    return value && !isParkingLabel(value) ? value : undefined
  }

  const route = getClean('route')
  const street = getClean('street_number') && route ? `${getClean('street_number')} ${route}` : route

  const city = [
    getClean('locality'),
    getClean('administrative_area_level_2'),
    getClean('administrative_area_level_1'),
    getClean('country'),
  ].find(Boolean)

  if (street) {
    return [street, city].filter(Boolean).join(', ')
  }

  return [
    getClean('neighborhood'),
    getClean('sublocality_level_1'),
    getClean('sublocality'),
    getClean('locality'),
    getClean('administrative_area_level_2'),
    getClean('administrative_area_level_1'),
    getClean('country'),
  ].find(Boolean) || ''
}

function isUnwantedResult(result = {}) {
  const types = result.types || []
  const formattedAddress = result.formatted_address || ''

  return (
    isPlusCodeLabel(formattedAddress)
    || isParkingLabel(formattedAddress)
    || UNWANTED_RESULT_TYPES.some((type) => types.includes(type))
  )
}

function pickPreferredGeocodedResult(results = []) {
  return (
    results.find((result) => {
      const types = result.types || []

      return !isUnwantedResult(result) && ['street_address', 'route'].some((type) => types.includes(type))
    })
    || results.find((result) => {
      const types = result.types || []

      return (
        !isUnwantedResult(result)
        && ['neighborhood', 'sublocality', 'sublocality_level_1', 'locality'].some((type) => types.includes(type))
      )
    })
    || results.find((result) => !isUnwantedResult(result))
    || results[0]
  )
}

function getReadableGeocodedLocation(results = []) {
  const preferredResult = pickPreferredGeocodedResult(results)
  const readableAddress = buildReadableLocationFromComponents(preferredResult || results[0] || {})

  if (readableAddress) {
    return readableAddress
  }

  const formattedAddress = preferredResult?.formatted_address || results[0]?.formatted_address || ''

  return normalizeDisplayedLocation(formattedAddress)
}

async function getPlaceDetails(placeId) {
  if (!placesService || !placeId) {
    return null
  }

  return new Promise((resolve) => {
    placesService.getDetails(
      {
        placeId,
        fields: ['name', 'formatted_address', 'address_components', 'geometry', 'plus_code', 'types'],
      },
      (place, status) => {
        if (status !== window.google.maps.places.PlacesServiceStatus.OK || !place) {
          resolve(null)
          return
        }

        resolve(place)
      },
    )
  })
}

async function initializePlaces() {
  if (autocompleteService && geocoder && placesService) {
    return
  }

  try {
    const maps = await loadGoogleMaps()
    autocompleteService = new maps.places.AutocompleteService()
    geocoder = new maps.Geocoder()
    placesSessionToken = new maps.places.AutocompleteSessionToken()
    placesService = new maps.places.PlacesService(document.createElement('div'))
  } catch (error) {
    locationError.value = error.message
  }
}

async function openLocationDialog() {
  isLocationDialogOpen.value = true
  locationError.value = ''
  locationSearchText.value =
    selectedLocation.value && selectedLocation.value !== 'Select location'
      ? selectedLocation.value
      : ''
  locationSuggestions.value = []

  await initializePlaces()
}

async function toggleLocationDialog() {
  if (isLocationDialogOpen.value) {
    closeLocationDialog()
    return
  }

  await openLocationDialog()
}

async function promptForCurrentLocation() {
  isLocationDialogOpen.value = true
  locationError.value = ''
  locationSearchText.value =
    selectedLocation.value && selectedLocation.value !== 'Select location'
      ? selectedLocation.value
      : ''
  locationSuggestions.value = []

  await initializePlaces()
  detectCurrentLocation()
}

function closeLocationDialog() {
  isLocationDialogOpen.value = false
}

function describeGeolocationError(error) {
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

function detectCurrentLocation() {
  locationError.value = ''

  if (!navigator.geolocation) {
    locationError.value = 'Current location is not supported in this browser.'
    return
  }

  if (!window.isSecureContext) {
    locationError.value = 'Location detection needs a secure (https://) connection. It will work once this site is served over https.'
    return
  }

  isDetectingLocation.value = true

  navigator.geolocation.getCurrentPosition(
    (position) => {
      const currentPosition = {
        lat: position.coords.latitude,
        lng: position.coords.longitude,
      }

      if (!geocoder) {
        locationError.value = 'Unable to resolve your exact address.'
        isDetectingLocation.value = false
        closeLocationDialog()
        return
      }

      geocoder.geocode({ location: currentPosition }, async (results, status) => {
        const exactAddress = status === 'OK' ? getReadableGeocodedLocation(results) : ''
        const geocodedResult = status === 'OK' ? pickPreferredGeocodedResult(results) : null
        const placeDetails = geocodedResult?.place_id
          ? await getPlaceDetails(geocodedResult.place_id)
          : null
        const displayLocation = buildReadableLocationFromComponents(placeDetails || geocodedResult || {})

        if (displayLocation) {
          setSelectedLocation(displayLocation)
        } else if (exactAddress) {
          setSelectedLocation(exactAddress)
        } else {
          locationError.value = 'Unable to resolve your exact address.'
        }

        isDetectingLocation.value = false
        closeLocationDialog()
      })
    },
    (error) => {
      locationError.value = describeGeolocationError(error)
      isDetectingLocation.value = false
    },
    {
      timeout: 10000,
    },
  )
}

async function selectSuggestion(suggestion) {
  await initializePlaces()

  const placeDetails = await getPlaceDetails(suggestion.id)
  const displayLocation = buildReadableLocationFromComponents(placeDetails || {})

  setSelectedLocation(displayLocation || suggestion.description)
  closeLocationDialog()
}

function submitTypedLocation() {
  const location = locationSearchText.value.trim()

  if (location) {
    setSelectedLocation(location)
    closeLocationDialog()
  }
}

function promptForLocationOnHome() {
  if (
    route.name !== 'home'
    || sessionStorage.getItem(AUTO_PROMPT_LOCATION_KEY) !== '1'
  ) {
    return
  }

  sessionStorage.removeItem(AUTO_PROMPT_LOCATION_KEY)
  promptForCurrentLocation()
}

watch(locationSearchText, async (value) => {
  const keyword = value.trim()

  if (!keyword || !autocompleteService) {
    locationSuggestions.value = []
    return
  }

  autocompleteService.getPlacePredictions(
    {
      input: keyword,
      sessionToken: placesSessionToken,
    },
    (predictions, status) => {
      if (status !== window.google.maps.places.PlacesServiceStatus.OK || !predictions) {
        locationSuggestions.value = []
        return
      }

      locationSuggestions.value = predictions.map((prediction) => ({
        id: prediction.place_id,
        mainText: prediction.structured_formatting.main_text,
        secondaryText: prediction.structured_formatting.secondary_text,
        description: prediction.description,
      }))
    },
  )
})

watch(
  () => route.name,
  (name) => {
    promptForLocationOnHome()

    if (
      hasAttemptedAutoLocation
      || name !== 'home'
      || localStorage.getItem(LOCATION_STORAGE_KEY)
    ) {
      return
    }

    hasAttemptedAutoLocation = true
    promptForCurrentLocation()
  },
  { immediate: true },
)

onMounted(() => {
  const storedLocation = localStorage.getItem(LOCATION_STORAGE_KEY)

  if (storedLocation) {
    setSelectedLocation(normalizeDisplayedLocation(storedLocation))
  }

  promptForLocationOnHome()
})
</script>

<template>
  <div class="location-picker">
    <button
      class="location-button"
      type="button"
      aria-haspopup="dialog"
      :aria-expanded="isLocationDialogOpen"
      @click="toggleLocationDialog"
    >
      <svg
        class="location-pin-icon"
        aria-hidden="true"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M20 10c0 5-8 12-8 12S4 15 4 10a8 8 0 1 1 16 0Z" />
        <circle cx="12" cy="10" r="3" />
      </svg>
      <span class="location-copy">
        <span class="action-label">Deliver to</span>
        <span class="location-row">
          <span class="location-name">{{ selectedLocation }}</span>
          <svg
            class="chevron"
            aria-hidden="true"
            viewBox="0 0 20 20"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="m6 8 4 4 4-4" />
          </svg>
        </span>
      </span>
    </button>

    <section
      v-if="isLocationDialogOpen"
      class="location-dialog"
      role="dialog"
      aria-modal="false"
      aria-labelledby="change-location-title"
    >
      <div class="location-dialog-header">
        <h2 id="change-location-title">Change Location</h2>
        <button
          class="location-dialog-close"
          type="button"
          aria-label="Close location dialog"
          @click="closeLocationDialog"
        >
          &times;
        </button>
      </div>

      <div class="location-dialog-controls">
        <button
          class="detect-location-button"
          type="button"
          @click="detectCurrentLocation"
        >
          {{ isDetectingLocation ? 'Detecting...' : 'Detect my location' }}
        </button>
        <span class="or-divider">OR</span>
        <form class="location-search-form" @submit.prevent="submitTypedLocation">
          <input
            v-model="locationSearchText"
            class="location-search-input"
            type="text"
            autofocus
            placeholder="Search delivery area"
          />
        </form>
      </div>

      <p v-if="locationError" class="form-message error-message">
        {{ locationError }}
      </p>

      <div class="location-suggestion-list">
        <button
          v-for="suggestion in locationSuggestions"
          :key="suggestion.id"
          class="location-suggestion"
          type="button"
          @click="selectSuggestion(suggestion)"
        >
          <span class="suggestion-pin" aria-hidden="true">⌖</span>
          <span>
            <strong>{{ suggestion.mainText }}</strong>
            <small>{{ suggestion.secondaryText }}</small>
          </span>
        </button>

        <button
          v-if="!locationSuggestions.length && locationSearchText"
          class="location-suggestion"
          type="button"
          @click="submitTypedLocation"
        >
          <span class="suggestion-pin" aria-hidden="true">⌖</span>
          <span>
            <strong>{{ locationSearchText }}</strong>
            <small>Use typed location</small>
          </span>
        </button>
      </div>
    </section>
  </div>
</template>
