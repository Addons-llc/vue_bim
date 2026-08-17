<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createWebsiteUser } from '../api/authApi'
import { loadGoogleMaps } from '../api/googleMaps'
import { currentUser } from '../data/authStore'
import { setCurrentUser } from '../data/authStore'
import {
  addCustomerAddress,
  customerAddresses,
  removeCustomerAddress,
  setDefaultCustomerAddress,
  updateCustomerAddress,
} from '../data/addressStore'

const route = useRoute()
const router = useRouter()
const fullName = ref('')
const email = ref('')
const errorMessage = ref('')
const successMessage = ref('')
const isSubmitting = ref(false)
const isAddressFormOpen = ref(false)
const isDetectingAddressLocation = ref(false)
const isAddressLocationEditedManually = ref(false)
const addressLocationError = ref('')
const editingAddressId = ref('')
const addressForm = ref({
  label: 'Home',
  contactName: '',
  phone: '',
  area: '',
  building: '',
  street: '',
  landmark: '',
  emirate: '',
  latitude: '',
  longitude: '',
  isDefault: false,
})
const appBase = import.meta.env.BASE_URL
const isCompletingProfile = computed(() => route.name === 'complete-profile')
const profileName = computed(() =>
  currentUser.value?.full_name
    || currentUser.value?.fullName
    || currentUser.value?.name
    || 'Customer',
)
const profileEmail = computed(() => currentUser.value?.email || '')
const profilePhone = computed(() =>
  currentUser.value?.mobile_no
    || currentUser.value?.phone
    || currentUser.value?.phoneNumber
    || '',
)

const phoneNumber = computed(() => {
  const routePhone = route.query.phone
  return Array.isArray(routePhone) ? routePhone[0] : routePhone || ''
})

const profileToken = computed(() => {
  const routeToken = route.query.token
  return Array.isArray(routeToken) ? routeToken[0] : routeToken || ''
})
const AUTO_PROMPT_LOCATION_KEY = 'buyInMinutesPromptLocationOnHome'
const UAE_COUNTRY_CODE = 'AE'
const UNWANTED_RESULT_TYPES = ['parking', 'point_of_interest', 'establishment']

let addressGeocoder
let addressPlaceApi

function resetAddressForm() {
  addressForm.value = {
    label: 'Home',
    contactName: profileName.value === 'Customer' ? '' : profileName.value,
    phone: profilePhone.value,
    area: '',
    building: '',
    street: '',
    landmark: '',
    emirate: '',
    latitude: '',
    longitude: '',
    isDefault: !customerAddresses.value.length,
  }
  editingAddressId.value = ''
  isAddressLocationEditedManually.value = false
  addressLocationError.value = ''
}

onMounted(() => {
  if (isCompletingProfile.value && !phoneNumber.value) {
    router.replace({ name: 'login' })
    return
  }

  if (!isCompletingProfile.value && !currentUser.value) {
    router.replace({ name: 'login' })
  }

  resetAddressForm()

  if (route.query.openAddress === '1') {
    isAddressFormOpen.value = true
  }
})

async function completeProfile() {
  errorMessage.value = ''
  successMessage.value = ''
  isSubmitting.value = true

  try {
    const payload = {
      email: email.value,
      fullName: fullName.value,
      phoneNumber: phoneNumber.value,
      profileToken: profileToken.value,
    }

    console.log('Website user profile payload', payload)
    const response = await createWebsiteUser(payload)
    console.log('Website user profile response', response)

    if (!response?.message?.success) {
      throw new Error(response?.message?.message || 'Unable to complete profile.')
    }

    const user = response.message.user || {}
    setCurrentUser(user)

    localStorage.setItem(
      'customerProfile',
      JSON.stringify({
        email: user.email || email.value.trim(),
        fullName: user.full_name || fullName.value.trim(),
        phoneNumber: user.mobile_no || phoneNumber.value,
      }),
    )

    successMessage.value = 'Profile created successfully.'
    sessionStorage.setItem(AUTO_PROMPT_LOCATION_KEY, '1')
    await router.push({ name: 'home' })
  } catch (error) {
    console.error('Website user creation failed', error)
    errorMessage.value = error.message
  } finally {
    isSubmitting.value = false
  }
}

function continueShopping() {
  sessionStorage.setItem(AUTO_PROMPT_LOCATION_KEY, '1')
  router.push({ name: 'home' })
}

function openAddressForm() {
  resetAddressForm()
  isAddressFormOpen.value = true
}

function editAddress(address) {
  addressForm.value = {
    label: address.label,
    contactName: address.contactName,
    phone: address.phone,
    area: address.area,
    building: address.building,
    street: address.street || '',
    landmark: address.landmark,
    emirate: address.emirate || '',
    latitude: address.latitude || '',
    longitude: address.longitude || '',
    isDefault: address.isDefault,
  }
  editingAddressId.value = address.id
  isAddressLocationEditedManually.value = false
  isAddressFormOpen.value = true
  addressLocationError.value = ''
}

function cancelAddressForm() {
  isAddressFormOpen.value = false
  resetAddressForm()
}

function markAddressEditedManually() {
  if (!addressForm.value.latitude && !addressForm.value.longitude) {
    return
  }

  addressForm.value = {
    ...addressForm.value,
    latitude: '',
    longitude: '',
  }
  isAddressLocationEditedManually.value = true
}

function saveAddress() {
  successMessage.value = ''
  errorMessage.value = ''

  if (editingAddressId.value) {
    updateCustomerAddress(editingAddressId.value, addressForm.value)
    successMessage.value = 'Address updated successfully.'
  } else {
    addCustomerAddress(addressForm.value)
    successMessage.value = 'Address added successfully.'
  }

  isAddressFormOpen.value = false
  resetAddressForm()
}

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

async function initializeAddressLocationServices() {
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

async function fillAddressFromCurrentLocation() {
  addressLocationError.value = ''
  successMessage.value = ''
  errorMessage.value = ''

  if (!navigator.geolocation) {
    addressLocationError.value = 'Current location is not supported in this browser.'
    return
  }

  if (!window.isSecureContext) {
    addressLocationError.value = 'Location detection needs a secure (https://) connection. It will work once this site is served over https.'
    return
  }

  const servicesReady = await initializeAddressLocationServices()

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
          isAddressLocationEditedManually.value = false
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
</script>

<template>
  <main class="auth-page">
    <section class="login-panel" :class="{ 'is-profile-view': !isCompletingProfile }">
      <a class="auth-brand" :href="appBase" aria-label="Buy In Minutes home">
        <img class="brand-logo" :src="`${appBase}bim.jpeg`" alt="" />
        <span class="brand-name">BIM</span>
      </a>

      <div class="login-heading">
        <p class="section-label">Profile</p>
        <h1>{{ isCompletingProfile ? 'Complete your details' : 'View profile' }}</h1>
        <p class="login-copy">
          {{ isCompletingProfile ? 'Add your name and email for faster checkout.' : 'Review your account details.' }}
        </p>
      </div>

      <section v-if="!isCompletingProfile" class="profile-view-panel">
        <div class="profile-view-row">
          <span>Full name</span>
          <strong>{{ profileName }}</strong>
        </div>
        <div class="profile-view-row">
          <span>Email address</span>
          <strong>{{ profileEmail || 'Not provided' }}</strong>
        </div>
        <div class="profile-view-row">
          <span>Phone number</span>
          <strong>{{ profilePhone || 'Not provided' }}</strong>
        </div>

        <section class="profile-address-section" aria-label="My addresses">
          <div class="profile-address-heading">
            <div>
              <span>My Addresses</span>
              <strong>{{ customerAddresses.length }} saved</strong>
            </div>
            <button class="profile-address-add-button" type="button" @click="openAddressForm">
              Add Address
            </button>
          </div>

          <div v-if="customerAddresses.length" class="profile-address-list">
            <article
              v-for="address in customerAddresses"
              :key="address.id"
              class="profile-address-card"
            >
              <header>
                <strong>{{ address.label }}</strong>
                <span v-if="address.isDefault">Default</span>
              </header>
              <p>{{ address.contactName }} · {{ address.phone }}</p>
              <p>{{ [address.street, address.building].filter(Boolean).join(', ') }}</p>
              <p>{{ [address.area, address.emirate].filter(Boolean).join(', ') }}</p>
              <p v-if="address.landmark">{{ address.landmark }}</p>
              <div class="profile-address-actions">
                <button
                  v-if="!address.isDefault"
                  type="button"
                  @click="setDefaultCustomerAddress(address.id)"
                >
                  Set default
                </button>
                <button type="button" @click="editAddress(address)">Edit</button>
                <button type="button" @click="removeCustomerAddress(address.id)">Delete</button>
              </div>
            </article>
          </div>

          <p v-else class="profile-address-empty">
            No saved addresses yet.
          </p>

          <form
            v-if="isAddressFormOpen"
            class="profile-address-form"
            @submit.prevent="saveAddress"
          >
            <label class="field-label" for="address-label">Address label</label>
            <select
              id="address-label"
              v-model="addressForm.label"
              class="form-input"
              required
            >
              <option value="Home">Home</option>
              <option value="Office">Office</option>
            </select>

            <label class="field-label" for="address-contact">Contact name</label>
            <input
              id="address-contact"
              v-model="addressForm.contactName"
              class="form-input"
              type="text"
              autocomplete="name"
              placeholder="Receiver name"
              required
            />

            <button
              class="profile-address-location-button"
              type="button"
              :disabled="isDetectingAddressLocation"
              @click="fillAddressFromCurrentLocation"
            >
              {{ isDetectingAddressLocation ? 'Detecting location...' : 'Use current location' }}
            </button>
            <p v-if="addressLocationError" class="form-message error-message profile-address-location-message">
              {{ addressLocationError }}
            </p>

            <label class="field-label" for="address-area">Area</label>
            <input
              id="address-area"
              v-model="addressForm.area"
              class="form-input"
              type="text"
              placeholder="Dubai Marina, Al Nahda, Business Bay"
              required
              @input="markAddressEditedManually"
            />

            <label class="field-label" for="address-building">Building / villa</label>
            <input
              id="address-building"
              v-model="addressForm.building"
              class="form-input"
              type="text"
              placeholder="Building, floor, apartment or villa number"
              required
              @input="markAddressEditedManually"
            />

            <label class="field-label" for="address-street">Street</label>
            <input
              id="address-street"
              v-model="addressForm.street"
              class="form-input"
              type="text"
              placeholder="Street name"
              @input="markAddressEditedManually"
            />

            <label class="field-label" for="address-landmark">Landmark</label>
            <input
              id="address-landmark"
              v-model="addressForm.landmark"
              class="form-input"
              type="text"
              placeholder="Nearby landmark"
              @input="markAddressEditedManually"
            />

            <label class="field-label" for="address-emirate">Emirate</label>
            <input
              id="address-emirate"
              v-model="addressForm.emirate"
              class="form-input"
              type="text"
              placeholder="Dubai, Abu Dhabi, Sharjah"
              @input="markAddressEditedManually"
            />

            <p v-if="addressForm.latitude && addressForm.longitude" class="profile-address-location-note">
              Location captured for this address.
            </p>
            <p v-else-if="isAddressLocationEditedManually" class="profile-address-location-note">
              Manual address details will be saved.
            </p>

            <label class="profile-address-default">
              <input v-model="addressForm.isDefault" type="checkbox" />
              <span>Use as default delivery address</span>
            </label>

            <div class="profile-address-form-actions">
              <button class="login-button" type="submit">
                {{ editingAddressId ? 'Update address' : 'Save address' }}
              </button>
              <button class="profile-address-cancel-button" type="button" @click="cancelAddressForm">
                Cancel
              </button>
            </div>
          </form>
        </section>

        <button class="login-button" type="button" @click="continueShopping">
          Continue shopping
        </button>
      </section>

      <form v-else class="login-form" @submit.prevent="completeProfile">
        <label class="field-label" for="full-name">Full name</label>
        <input
          id="full-name"
          v-model="fullName"
          class="form-input"
          type="text"
          autocomplete="name"
          placeholder="Enter full name"
          required
        />

        <label class="field-label" for="email">Email address</label>
        <input
          id="email"
          v-model="email"
          class="form-input"
          type="email"
          autocomplete="email"
          placeholder="name@example.com"
          required
        />

        <button class="login-button" type="submit" :disabled="isSubmitting">
          {{ isSubmitting ? 'Creating account...' : 'Continue shopping' }}
        </button>
      </form>

      <p v-if="successMessage" class="form-message success-message">
        {{ successMessage }}
      </p>
      <p v-if="errorMessage" class="form-message error-message">
        {{ errorMessage }}
      </p>
    </section>
  </main>
</template>
