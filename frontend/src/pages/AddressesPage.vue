<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AddressCard from '../components/profile/AddressCard.vue'
import AddressForm from '../components/profile/AddressForm.vue'
import { useAddressLocation } from '../composables/useAddressLocation'
import {
  addCustomerAddress,
  customerAddresses,
  removeCustomerAddress,
  setDefaultCustomerAddress,
  updateCustomerAddress,
} from '../data/addressStore'
import { currentUser } from '../data/authStore'

const route = useRoute()
const router = useRouter()
const { addressLocationError, fillAddressFromCurrentLocation, isDetectingAddressLocation } = useAddressLocation()

const isAddressFormOpen = ref(false)
const isAddressLocationEditedManually = ref(false)
const editingAddressId = ref('')
const addressForm = ref(createAddressForm())
const toast = ref({ message: '', tone: 'success', id: 0 })
let toastTimer = null

const isReturningToCart = computed(() => route.query.returnTo === 'cart')
const backLink = computed(() =>
  isReturningToCart.value
    ? { label: 'Back to cart', to: { name: 'cart' } }
    : { label: 'Back to profile', to: { name: 'profile' } },
)
const addressCountLabel = computed(() => {
  const count = customerAddresses.value.length

  return `${count} saved ${count === 1 ? 'address' : 'addresses'}`
})

function showToast(message) {
  clearTimeout(toastTimer)
  toast.value = { message, tone: 'success', id: toast.value.id + 1 }
  toastTimer = setTimeout(() => {
    toast.value = { ...toast.value, message: '' }
  }, 2400)
}

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

function resetAddressForm() {
  const user = currentUser.value

  addressForm.value = createAddressForm({
    contactName: user?.full_name || user?.fullName || user?.name || '',
    phone: user?.mobile_no || user?.phone || user?.phoneNumber || '',
    email: user?.email || '',
    isDefault: !customerAddresses.value.length,
  })
  editingAddressId.value = ''
  isAddressLocationEditedManually.value = false
  addressLocationError.value = ''
}

function showAddressForm() {
  isAddressFormOpen.value = true
  window.scrollTo({ top: 0 })
}

function closeAddressForm() {
  isAddressFormOpen.value = false
  resetAddressForm()
  window.scrollTo({ top: 0 })
}

function openAddressForm() {
  resetAddressForm()
  showAddressForm()
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
  addressLocationError.value = ''
  showAddressForm()
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
  if (editingAddressId.value) {
    updateCustomerAddress(editingAddressId.value, addressForm.value)
    showToast('Address updated')
  } else {
    addCustomerAddress(addressForm.value)
    showToast('Address added')
  }

  closeAddressForm()

  if (isReturningToCart.value) {
    router.push({ name: 'cart' })
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

onMounted(() => {
  if (!currentUser.value) {
    router.replace({ name: 'login' })
    return
  }

  resetAddressForm()

  if (route.query.add === '1') {
    isAddressFormOpen.value = true
  }
})

onBeforeUnmount(() => {
  clearTimeout(toastTimer)
})
</script>

<template>
  <section class="addresses-page">
    <RouterLink class="addresses-back-link" :to="backLink.to">
      <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
        <path d="m15 6-6 6 6 6" />
      </svg>
      {{ backLink.label }}
    </RouterLink>

    <template v-if="isAddressFormOpen">
      <header class="addresses-heading">
        <h1>{{ editingAddressId ? 'Edit address' : 'Add new address' }}</h1>
      </header>

      <AddressForm
        v-model:form="addressForm"
        :address-location-error="addressLocationError"
        :is-address-location-edited-manually="isAddressLocationEditedManually"
        :is-detecting-address-location="isDetectingAddressLocation"
        :is-editing="Boolean(editingAddressId)"
        @cancel="closeAddressForm"
        @edited="markAddressEditedManually"
        @submit="saveAddress"
        @use-current-location="handleUseCurrentLocation"
      />
    </template>

    <template v-else>
      <header class="addresses-heading">
        <h1>Saved addresses</h1>
        <p>{{ addressCountLabel }}</p>
      </header>

      <button class="account-add-address" type="button" @click="openAddressForm">
        <span aria-hidden="true">+</span>
        Add new address
      </button>

      <TransitionGroup
        v-if="customerAddresses.length"
        name="account-list"
        tag="div"
        class="account-address-list"
      >
        <AddressCard
          v-for="address in customerAddresses"
          :key="address.id"
          :address="address"
          @set-default="handleSetDefaultAddress"
          @edit="editAddress"
          @delete="handleDeleteAddress"
        />
      </TransitionGroup>

      <p v-else class="account-empty">
        No saved addresses yet. Add one for faster checkout.
      </p>
    </template>

    <Teleport to="body">
      <Transition name="account-toast">
        <div
          v-if="toast.message"
          :key="toast.id"
          class="account-toast"
          role="status"
        >
          {{ toast.message }}
        </div>
      </Transition>
    </Teleport>
  </section>
</template>
