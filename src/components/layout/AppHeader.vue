<script setup>
import { computed, ref, watch } from 'vue'
import { loadGoogleMaps } from '../../api/googleMaps'
import { cartItemCount } from '../../data/cartStore'

const emit = defineEmits(['cart', 'logout', 'search'])

const selectedLocation = ref('Select location')
const isLocationDialogOpen = ref(false)
const isDetectingLocation = ref(false)
const locationError = ref('')
const locationSearchText = ref('')
const locationSuggestions = ref([])
const searchText = ref('')
const appBase = import.meta.env.BASE_URL

let autocompleteService
let geocoder
let placesSessionToken

const searchMessage = computed(() => {
  const keyword = searchText.value.trim()

  if (!keyword) {
    return 'Search vegetables, fruits, grocery, meat, fish'
  }

  return `Searching for "${keyword}"`
})

async function openLocationDialog() {
  isLocationDialogOpen.value = true
  locationError.value = ''
  locationSearchText.value = ''
  locationSuggestions.value = []

  await initializePlaces()
}

function closeLocationDialog() {
  isLocationDialogOpen.value = false
}

async function initializePlaces() {
  if (autocompleteService && geocoder) {
    return
  }

  try {
    const maps = await loadGoogleMaps()
    autocompleteService = new maps.places.AutocompleteService()
    geocoder = new maps.Geocoder()
    placesSessionToken = new maps.places.AutocompleteSessionToken()
  } catch (error) {
    locationError.value = error.message
  }
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

function detectCurrentLocation() {
  locationError.value = ''

  if (!navigator.geolocation) {
    locationError.value = 'Current location is not supported in this browser.'
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
        selectedLocation.value = 'Current location'
        isDetectingLocation.value = false
        closeLocationDialog()
        return
      }

      geocoder.geocode({ location: currentPosition }, (results, status) => {
        selectedLocation.value =
          status === 'OK' && results[0] ? results[0].formatted_address : 'Current location'
        isDetectingLocation.value = false
        closeLocationDialog()
      })
    },
    () => {
      locationError.value = 'Unable to access your current location.'
      isDetectingLocation.value = false
    },
  )
}

function selectSuggestion(suggestion) {
  selectedLocation.value = suggestion.description
  closeLocationDialog()
}

function submitTypedLocation() {
  const location = locationSearchText.value.trim()

  if (location) {
    selectedLocation.value = location
    closeLocationDialog()
  }
}

function handleSearch() {
  const keyword = searchText.value.trim()

  emit('search', keyword)
}

function handleLogout() {
  emit('logout')
}

function openCart() {
  emit('cart')
}
</script>

<template>
  <header class="app-header">
    <div class="header-inner">
      <a class="brand" :href="appBase" aria-label="Buy in Minutes home">
        <img class="brand-logo" :src="`${appBase}bim.jpeg`" alt="" />
        <span class="brand-text">
          <span class="brand-name">BUY IN MINUTES</span>
          <span class="brand-tagline">Fresh market delivery</span>
        </span>
      </a>

      <div class="location-picker">
        <button
          class="location-button"
          type="button"
          aria-haspopup="dialog"
          :aria-expanded="isLocationDialogOpen"
          @click="openLocationDialog"
        >
          <span class="action-icon" aria-hidden="true">⌖</span>
          <span class="location-copy">
            <span class="action-label">Deliver to</span>
            <span class="location-name">{{ selectedLocation }}</span>
          </span>
          <span class="chevron" aria-hidden="true">⌄</span>
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
              ×
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

      <form class="search-form" role="search" @submit.prevent="handleSearch">
        <label class="visually-hidden" for="site-search">Search products</label>
        <span class="search-icon" aria-hidden="true">⌕</span>
        <input
          id="site-search"
          v-model="searchText"
          class="search-input"
          type="search"
          placeholder="Search vegetables, fruits, grocery, meat, fish"
        />
        <button class="search-button" type="submit">Search</button>
        <p class="visually-hidden" aria-live="polite">{{ searchMessage }}</p>
      </form>

      <nav class="header-actions" aria-label="Account and shopping">
        <button
          class="header-action-button cart-link"
          type="button"
          :disabled="!cartItemCount"
          :aria-disabled="!cartItemCount"
          @click="openCart"
        >
          <svg
            class="action-svg"
            aria-hidden="true"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <circle cx="8" cy="21" r="1" />
            <circle cx="19" cy="21" r="1" />
            <path d="M2 2h3l3 13h10l3-8H7" />
          </svg>
          <span>Cart</span>
          <span class="cart-count" :aria-label="`${cartItemCount} items in cart`">
            {{ cartItemCount }}
          </span>
        </button>

        <button class="logout-button" type="button" @click="handleLogout">
          <svg
            class="action-svg"
            aria-hidden="true"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
            <path d="M16 17l5-5-5-5" />
            <path d="M21 12H9" />
          </svg>
          <span>Logout</span>
        </button>
      </nav>
    </div>
  </header>

</template>
