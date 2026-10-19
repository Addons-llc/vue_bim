<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createWebsiteUser, logout } from '../api/authApi'
import { getOrderHistory } from '../api/orderHistoryApi'
import { cartItemCount } from '../data/cartStore'
import { wishlistItemCount } from '../data/wishlistStore'
import { currentUser } from '../data/authStore'
import { setCurrentUser } from '../data/authStore'
import {
  addCustomerAddress,
  customerAddresses,
  removeCustomerAddress,
  setDefaultCustomerAddress,
  updateCustomerAddress,
} from '../data/addressStore'
import AddressCard from '../components/profile/AddressCard.vue'
import AddressForm from '../components/profile/AddressForm.vue'
import { useAddressLocation } from '../composables/useAddressLocation'

const route = useRoute()
const router = useRouter()
const fullName = ref('')
const email = ref('')
const errorMessage = ref('')
const successMessage = ref('')
const isSubmitting = ref(false)
const isAddressFormOpen = ref(false)
const isAddressLocationEditedManually = ref(false)
const editingAddressId = ref('')
const { addressLocationError, fillAddressFromCurrentLocation, isDetectingAddressLocation } = useAddressLocation()
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
const SUPPLIER_QUOTATION_HISTORY_TYPE = 'supplier_quotation'

const orders = ref([])
const isLoadingOrders = ref(false)
const hasOrdersError = ref(false)
const isAddressSectionOpen = ref(false)
const isLogoutSheetOpen = ref(false)
const isLoggingOut = ref(false)
const toast = ref({ message: '', tone: 'success', id: 0 })
const addressSectionRef = ref(null)
let toastTimer = null

const profileInitials = computed(() => {
  const parts = profileName.value.trim().split(/\s+/).filter(Boolean)
  const initials = parts.slice(0, 2).map((part) => part[0]).join('')

  return (initials || 'C').toUpperCase()
})
const greeting = computed(() => {
  const hour = new Date().getHours()

  if (hour < 12) {
    return 'Good morning'
  }

  return hour < 17 ? 'Good afternoon' : 'Good evening'
})
const firstName = computed(() => profileName.value.trim().split(/\s+/)[0] || 'there')
const salesOrders = computed(() =>
  orders.value.filter((order) => order.historyType !== SUPPLIER_QUOTATION_HISTORY_TYPE),
)
const latestOrder = computed(() => salesOrders.value[0] || null)
const defaultAddress = computed(() =>
  customerAddresses.value.find((address) => address.isDefault) || customerAddresses.value[0] || null,
)
const profileCompletion = computed(() => {
  const checks = [
    profileName.value && profileName.value !== 'Customer',
    profileEmail.value,
    profilePhone.value,
    customerAddresses.value.length,
  ]

  return Math.round((checks.filter(Boolean).length / checks.length) * 100)
})
const accountStats = computed(() => [
  {
    key: 'orders',
    label: 'Orders',
    value: isLoadingOrders.value ? null : hasOrdersError.value ? '–' : salesOrders.value.length,
  },
  { key: 'wishlist', label: 'Wishlist', value: wishlistItemCount.value },
  { key: 'cart', label: 'In cart', value: cartItemCount.value },
  { key: 'addresses', label: 'Addresses', value: customerAddresses.value.length },
])

function showToast(message, tone = 'success') {
  clearTimeout(toastTimer)
  toast.value = { message, tone, id: toast.value.id + 1 }
  toastTimer = setTimeout(() => {
    toast.value = { ...toast.value, message: '' }
  }, 2600)
}

async function loadOrders() {
  if (!currentUser.value) {
    return
  }

  isLoadingOrders.value = true
  hasOrdersError.value = false

  try {
    const response = await getOrderHistory()
    orders.value = response?.message || []
  } catch (error) {
    console.error('Unable to load order summary', error)
    hasOrdersError.value = true
  } finally {
    isLoadingOrders.value = false
  }
}

function formatOrderDate(value) {
  if (!value) {
    return ''
  }

  const date = new Date(value)

  return Number.isNaN(date.getTime())
    ? String(value)
    : date.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
}

function formatAmount(amount, currency = 'AED') {
  return `${currency} ${Number(amount || 0).toFixed(2)}`
}

function getStatusTone(status) {
  const normalized = String(status || '').toLowerCase()

  if (['completed', 'delivered', 'closed', 'paid'].some((word) => normalized.includes(word))) {
    return 'success'
  }

  if (['cancel', 'fail', 'reject'].some((word) => normalized.includes(word))) {
    return 'danger'
  }

  return 'pending'
}

async function openAddressSection() {
  isAddressSectionOpen.value = true
  await nextTick()
  addressSectionRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function handleStatTap(key) {
  if (key === 'orders') {
    router.push({ name: 'orders' })
  } else if (key === 'wishlist') {
    router.push({ name: 'wishlist' })
  } else if (key === 'cart') {
    router.push({ name: 'cart' })
  } else {
    openAddressSection()
  }
}

async function copyToClipboard(value, label) {
  if (!value) {
    return
  }

  try {
    await navigator.clipboard.writeText(value)
    showToast(`${label} copied`)
  } catch {
    showToast(`Unable to copy ${label.toLowerCase()}`, 'error')
  }
}

function handleSetDefaultAddress(addressId) {
  setDefaultCustomerAddress(addressId)
  showToast('Default address updated')
}

function handleDeleteAddress(addressId) {
  removeCustomerAddress(addressId)
  showToast('Address deleted')
}

async function confirmLogout() {
  isLoggingOut.value = true

  try {
    await logout()
  } catch (error) {
    console.error('Logout failed', error)
  } finally {
    isLoggingOut.value = false
    isLogoutSheetOpen.value = false
    router.push({ name: 'login' })
  }
}

onBeforeUnmount(() => {
  clearTimeout(toastTimer)
})

function createAddressForm(overrides = {}) {
  return {
    label: 'Home',
    contactName: '',
    phone: '',
    email: '',
    area: '',
    apartmentOfficeName: '',
    apartmentOfficeNo: '',
    building: '',
    street: '',
    landmark: '',
    emirate: '',
    latitude: '',
    longitude: '',
    isDefault: false,
    ...overrides,
  }
}

const addressForm = ref(createAddressForm())

function resetAddressForm() {
  addressForm.value = createAddressForm({
    contactName: profileName.value === 'Customer' ? '' : profileName.value,
    phone: profilePhone.value,
    email: profileEmail.value,
    isDefault: !customerAddresses.value.length,
  })
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
    isAddressSectionOpen.value = true
  }

  if (!isCompletingProfile.value) {
    loadOrders()
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
  isAddressSectionOpen.value = true
}

function editAddress(address) {
  addressForm.value = createAddressForm({
    label: address.label,
    contactName: address.contactName,
    phone: address.phone,
    email: address.email || '',
    area: address.area,
    apartmentOfficeName: address.apartmentOfficeName || '',
    apartmentOfficeNo: address.apartmentOfficeNo || '',
    building: address.building,
    street: address.street || '',
    landmark: address.landmark,
    emirate: address.emirate || '',
    latitude: address.latitude || '',
    longitude: address.longitude || '',
    isDefault: address.isDefault,
  })
  editingAddressId.value = address.id
  isAddressLocationEditedManually.value = false
  isAddressFormOpen.value = true
  isAddressSectionOpen.value = true
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

function handleUseCurrentLocation() {
  fillAddressFromCurrentLocation(addressForm)
}

function saveAddress() {
  successMessage.value = ''
  errorMessage.value = ''

  if (editingAddressId.value) {
    updateCustomerAddress(editingAddressId.value, addressForm.value)
    showToast('Address updated')
  } else {
    addCustomerAddress(addressForm.value)
    showToast('Address added')
  }

  isAddressFormOpen.value = false
  resetAddressForm()
}
</script>

<template>
  <section v-if="!isCompletingProfile" class="account-page">
    <header class="account-hero">
      <div class="account-hero-top">
        <div class="account-hero-avatar" aria-hidden="true">
          <span>{{ profileInitials }}</span>
          <svg class="account-hero-avatar-ring" viewBox="0 0 36 36">
            <circle class="account-hero-avatar-ring-track" cx="18" cy="18" r="16.5" />
            <circle
              class="account-hero-avatar-ring-fill"
              cx="18"
              cy="18"
              r="16.5"
              :style="{ strokeDasharray: `${profileCompletion * 1.037} 103.7` }"
            />
          </svg>
        </div>
        <div class="account-hero-text">
          <p>{{ greeting }}, {{ firstName }} 👋</p>
          <h1>{{ profileName }}</h1>
          <span class="account-completion">Profile {{ profileCompletion }}% complete</span>
        </div>
      </div>

      <div class="account-contact-chips">
        <button
          v-if="profilePhone"
          class="account-chip"
          type="button"
          title="Copy phone number"
          @click="copyToClipboard(profilePhone, 'Phone number')"
        >
          <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2Z" />
          </svg>
          {{ profilePhone }}
        </button>
        <button
          v-if="profileEmail"
          class="account-chip"
          type="button"
          title="Copy email"
          @click="copyToClipboard(profileEmail, 'Email')"
        >
          <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="4" width="20" height="16" rx="2" />
            <path d="m22 7-10 6L2 7" />
          </svg>
          {{ profileEmail }}
        </button>
      </div>
    </header>

    <div class="account-stats" role="list">
      <button
        v-for="stat in accountStats"
        :key="stat.key"
        class="account-stat"
        :class="`is-${stat.key}`"
        type="button"
        role="listitem"
        @click="handleStatTap(stat.key)"
      >
        <span v-if="stat.value === null" class="account-skeleton" aria-label="Loading" />
        <strong v-else>{{ stat.value }}</strong>
        <span>{{ stat.label }}</span>
      </button>
    </div>

    <button
      v-if="latestOrder"
      class="account-latest-order"
      type="button"
      @click="router.push({ name: 'order-details', params: { orderName: latestOrder.name } })"
    >
      <span class="account-latest-order-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M7 3h10l2 4v14H5V7l2-4Z" />
          <path d="M7 7h10M9 12h6M9 16h4" />
        </svg>
      </span>
      <span class="account-latest-order-text">
        <small>Latest order · {{ formatOrderDate(latestOrder.transactionDate) }}</small>
        <strong>{{ latestOrder.name }}</strong>
        <span>{{ latestOrder.items.length }} item{{ latestOrder.items.length === 1 ? '' : 's' }} · {{ formatAmount(latestOrder.grandTotal, latestOrder.currency) }}</span>
      </span>
      <span v-if="latestOrder.status" class="account-status" :class="`is-${getStatusTone(latestOrder.status)}`">
        {{ latestOrder.status }}
      </span>
    </button>
    <div v-else-if="isLoadingOrders" class="account-latest-order is-loading" aria-hidden="true">
      <span class="account-skeleton is-block" />
    </div>

    <nav class="account-links" aria-label="Account">
      <RouterLink class="account-links-row" :to="{ name: 'orders' }">
        <span class="account-links-icon is-blue" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M7 3h10l2 4v14H5V7l2-4Z" />
            <path d="M7 7h10M9 12h6M9 16h4" />
          </svg>
        </span>
        <span class="account-links-text">
          <strong>My orders</strong>
          <small>Track, reorder and review purchases</small>
        </span>
        <svg class="account-chevron is-right" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
          <path d="m9 6 6 6-6 6" />
        </svg>
      </RouterLink>

      <RouterLink class="account-links-row" :to="{ name: 'wishlist' }">
        <span class="account-links-icon is-pink" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 14c1.5-1.5 3-3.2 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.8 0-3 .5-4.5 2-1.5-1.5-2.7-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4 3 5.5l7 7Z" />
          </svg>
        </span>
        <span class="account-links-text">
          <strong>Wishlist</strong>
          <small>{{ wishlistItemCount ? `${wishlistItemCount} saved item${wishlistItemCount === 1 ? '' : 's'}` : 'Save products you love' }}</small>
        </span>
        <svg class="account-chevron is-right" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
          <path d="m9 6 6 6-6 6" />
        </svg>
      </RouterLink>

      <div ref="addressSectionRef" class="account-links-group" :class="{ 'is-open': isAddressSectionOpen }">
        <button
          class="account-links-row"
          type="button"
          :aria-expanded="isAddressSectionOpen"
          @click="isAddressSectionOpen = !isAddressSectionOpen"
        >
          <span class="account-links-icon is-green" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 21s-7-6.2-7-12a7 7 0 0 1 14 0c0 5.8-7 12-7 12Z" />
              <circle cx="12" cy="9" r="2.5" />
            </svg>
          </span>
          <span class="account-links-text">
            <strong>Saved addresses</strong>
            <small>
              {{ defaultAddress ? `Default: ${defaultAddress.label}${defaultAddress.area ? ` · ${defaultAddress.area}` : ''}` : 'Add a delivery address' }}
            </small>
          </span>
          <span class="account-count-pill">{{ customerAddresses.length }}</span>
          <svg class="account-chevron" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
            <path d="m6 9 6 6 6-6" />
          </svg>
        </button>

        <div class="account-collapse" :class="{ 'is-open': isAddressSectionOpen }">
          <div class="account-collapse-inner">
            <div class="account-address-panel">
              <TransitionGroup v-if="customerAddresses.length" name="account-list" tag="div" class="account-address-list">
                <AddressCard
                  v-for="address in customerAddresses"
                  :key="address.id"
                  :address="address"
                  @set-default="handleSetDefaultAddress"
                  @edit="editAddress"
                  @delete="handleDeleteAddress"
                />
              </TransitionGroup>

              <p v-else-if="!isAddressFormOpen" class="account-empty">
                No saved addresses yet. Add one for faster checkout.
              </p>

              <AddressForm
                v-if="isAddressFormOpen"
                v-model:form="addressForm"
                :address-location-error="addressLocationError"
                :is-address-location-edited-manually="isAddressLocationEditedManually"
                :is-detecting-address-location="isDetectingAddressLocation"
                :is-editing="Boolean(editingAddressId)"
                @cancel="cancelAddressForm"
                @edited="markAddressEditedManually"
                @submit="saveAddress"
                @use-current-location="handleUseCurrentLocation"
              />

              <button v-else class="account-add-address" type="button" @click="openAddressForm">
                <span aria-hidden="true">+</span>
                Add new address
              </button>
            </div>
          </div>
        </div>
      </div>

      <RouterLink class="account-links-row" :to="{ name: 'cart' }">
        <span class="account-links-icon is-amber" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="8" cy="21" r="1" />
            <circle cx="19" cy="21" r="1" />
            <path d="M2 2h3l3 13h10l3-8H7" />
          </svg>
        </span>
        <span class="account-links-text">
          <strong>Cart</strong>
          <small>{{ cartItemCount ? `${cartItemCount} item${cartItemCount === 1 ? '' : 's'} waiting for checkout` : 'Your cart is empty' }}</small>
        </span>
        <svg class="account-chevron is-right" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
          <path d="m9 6 6 6-6 6" />
        </svg>
      </RouterLink>
    </nav>

    <div class="account-footer-actions">
      <button class="account-primary-button" type="button" @click="continueShopping">
        Continue shopping
      </button>
      <button class="account-logout-button" type="button" @click="isLogoutSheetOpen = true">
        <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
          <path d="m16 17 5-5-5-5M21 12H9" />
        </svg>
        Log out
      </button>
    </div>

    <Teleport to="body">
      <Transition name="account-sheet">
        <div
          v-if="isLogoutSheetOpen"
          class="account-sheet-backdrop"
          @click.self="isLogoutSheetOpen = false"
        >
          <div class="account-sheet" role="dialog" aria-modal="true" aria-labelledby="account-logout-title">
            <span class="account-sheet-handle" aria-hidden="true" />
            <h2 id="account-logout-title">Log out of BIM?</h2>
            <p>Your cart and wishlist stay saved on this device.</p>
            <div class="account-sheet-actions">
              <button class="is-ghost" type="button" @click="isLogoutSheetOpen = false">Cancel</button>
              <button class="is-danger" type="button" :disabled="isLoggingOut" @click="confirmLogout">
                {{ isLoggingOut ? 'Logging out…' : 'Log out' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>

      <Transition name="account-toast">
        <div
          v-if="toast.message"
          :key="toast.id"
          class="account-toast"
          :class="`is-${toast.tone}`"
          role="status"
        >
          {{ toast.message }}
        </div>
      </Transition>
    </Teleport>
  </section>

  <main v-else class="auth-page">
    <section class="login-panel">
      <a class="auth-brand" :href="appBase" aria-label="Buy In Minutes home">
        <img class="brand-logo" :src="`${appBase}bim.jpeg`" alt="" />
        <span class="brand-name">BIM</span>
      </a>

      <div class="login-heading">
        <p class="section-label">Profile</p>
        <h1>Complete your details</h1>
        <p class="login-copy">Add your name and email for faster checkout.</p>
      </div>

      <form class="login-form" @submit.prevent="completeProfile">
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
