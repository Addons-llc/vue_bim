<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createWebsiteUser } from '../api/authApi'
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
const editingAddressId = ref('')
const addressForm = ref({
  label: 'Home',
  contactName: '',
  phone: '',
  area: '',
  building: '',
  landmark: '',
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

function resetAddressForm() {
  addressForm.value = {
    label: 'Home',
    contactName: profileName.value === 'Customer' ? '' : profileName.value,
    phone: profilePhone.value,
    area: '',
    building: '',
    landmark: '',
    isDefault: !customerAddresses.value.length,
  }
  editingAddressId.value = ''
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
    landmark: address.landmark,
    isDefault: address.isDefault,
  }
  editingAddressId.value = address.id
  isAddressFormOpen.value = true
}

function cancelAddressForm() {
  isAddressFormOpen.value = false
  resetAddressForm()
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
              <p>{{ address.building }}, {{ address.area }}</p>
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

            <label class="field-label" for="address-phone">Phone number</label>
            <input
              id="address-phone"
              v-model="addressForm.phone"
              class="form-input"
              type="tel"
              autocomplete="tel"
              placeholder="Delivery contact number"
              required
            />

            <label class="field-label" for="address-area">Area</label>
            <input
              id="address-area"
              v-model="addressForm.area"
              class="form-input"
              type="text"
              placeholder="Dubai Marina, Al Nahda, Business Bay"
              required
            />

            <label class="field-label" for="address-building">Building / villa</label>
            <input
              id="address-building"
              v-model="addressForm.building"
              class="form-input"
              type="text"
              placeholder="Building, floor, apartment or villa number"
              required
            />

            <label class="field-label" for="address-landmark">Landmark</label>
            <input
              id="address-landmark"
              v-model="addressForm.landmark"
              class="form-input"
              type="text"
              placeholder="Nearby landmark"
            />

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
