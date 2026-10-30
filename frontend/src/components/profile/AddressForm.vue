<script setup>
import { computed, nextTick, ref } from 'vue'

const form = defineModel('form', {
  type: Object,
  required: true,
})

defineProps({
  addressLocationError: {
    type: String,
    default: '',
  },
  isAddressLocationEditedManually: {
    type: Boolean,
    default: false,
  },
  isDetectingAddressLocation: {
    type: Boolean,
    default: false,
  },
  isEditing: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['cancel', 'edited', 'submit', 'use-current-location'])

const ADDRESS_TYPES = [
  { value: 'Home', paths: ['M3 11l9-8 9 8', 'M5 10v10h14V10'] },
  { value: 'Office', paths: ['M6 3h12v18H6z', 'M10 7h1M13 7h1M10 11h1M13 11h1', 'M10 21v-4h4v4'] },
]
const FIELD_IDS = {
  contactName: 'address-contact',
  phone: 'address-phone',
  email: 'address-email',
  apartmentOfficeName: 'address-apartment-office-name',
  apartmentOfficeNo: 'address-apartment-office-no',
  building: 'address-building',
}
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const MINIMUM_PHONE_DIGITS = 7

const touchedFields = ref({})
const hasTriedSubmit = ref(false)

const apartmentOfficeNameLabel = computed(() =>
  form.value.label === 'Office' ? 'Office name' : 'Apartment name',
)
const apartmentOfficeNoLabel = computed(() =>
  form.value.label === 'Office' ? 'Office no' : 'Apartment no',
)
const apartmentOfficeNamePlaceholder = computed(() =>
  form.value.label === 'Office' ? 'Office or company name' : 'Apartment or residence name',
)
const apartmentOfficeNoPlaceholder = computed(() =>
  form.value.label === 'Office' ? 'Office number' : 'Apartment number',
)
const hasCapturedLocation = computed(() => Boolean(form.value.latitude && form.value.longitude))

const fieldErrors = computed(() => {
  const value = form.value
  const errors = {}
  const phone = String(value.phone || '').trim()
  const email = String(value.email || '').trim()

  if (!String(value.contactName || '').trim()) {
    errors.contactName = 'Enter the receiver name.'
  }

  if (!phone) {
    errors.phone = 'Enter a phone number.'
  } else if (phone.replace(/\D/g, '').length < MINIMUM_PHONE_DIGITS) {
    errors.phone = 'Enter a valid phone number.'
  }

  if (email && !EMAIL_PATTERN.test(email)) {
    errors.email = 'Enter a valid email address.'
  }

  if (!String(value.apartmentOfficeName || '').trim()) {
    errors.apartmentOfficeName = `Enter the ${apartmentOfficeNameLabel.value.toLowerCase()}.`
  }

  if (!String(value.apartmentOfficeNo || '').trim()) {
    errors.apartmentOfficeNo = `Enter the ${apartmentOfficeNoLabel.value.toLowerCase()}.`
  }

  if (!String(value.building || '').trim()) {
    errors.building = 'Enter the building or villa.'
  }

  return errors
})

function getFieldError(field) {
  return touchedFields.value[field] || hasTriedSubmit.value ? fieldErrors.value[field] || '' : ''
}

function markFieldTouched(field) {
  touchedFields.value = { ...touchedFields.value, [field]: true }
}

async function submitForm() {
  hasTriedSubmit.value = true

  const firstInvalidField = Object.keys(FIELD_IDS).find((field) => fieldErrors.value[field])

  if (!firstInvalidField) {
    emit('submit')
    return
  }

  await nextTick()
  document.getElementById(FIELD_IDS[firstInvalidField])?.focus()
}
</script>

<template>
  <form class="profile-address-form" novalidate @submit.prevent="submitForm">
    <fieldset class="address-form-types">
      <legend class="field-label">Save address as</legend>
      <div class="address-form-type-list">
        <label
          v-for="addressType in ADDRESS_TYPES"
          :key="addressType.value"
          class="address-form-type"
          :class="{ 'is-selected': form.label === addressType.value }"
        >
          <input v-model="form.label" type="radio" name="address-label" :value="addressType.value" />
          <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path v-for="path in addressType.paths" :key="path" :d="path" />
          </svg>
          <span>{{ addressType.value }}</span>
        </label>
      </div>
    </fieldset>

    <section class="address-form-section" aria-labelledby="address-contact-title">
      <h2 id="address-contact-title">Contact details</h2>

      <div class="address-form-field" :class="{ 'has-error': getFieldError('contactName') }">
        <label class="field-label" for="address-contact">Contact name</label>
        <input
          id="address-contact"
          v-model="form.contactName"
          class="form-input"
          type="text"
          autocomplete="name"
          placeholder="Receiver name"
          :aria-invalid="Boolean(getFieldError('contactName'))"
          aria-describedby="address-contact-error"
          @blur="markFieldTouched('contactName')"
        />
        <p v-if="getFieldError('contactName')" id="address-contact-error" class="address-form-error">
          {{ getFieldError('contactName') }}
        </p>
      </div>

      <div class="address-form-field" :class="{ 'has-error': getFieldError('phone') }">
        <label class="field-label" for="address-phone">Phone number</label>
        <input
          id="address-phone"
          v-model="form.phone"
          class="form-input"
          type="tel"
          inputmode="tel"
          autocomplete="tel"
          placeholder="50 123 4567"
          :aria-invalid="Boolean(getFieldError('phone'))"
          aria-describedby="address-phone-error"
          @blur="markFieldTouched('phone')"
        />
        <p v-if="getFieldError('phone')" id="address-phone-error" class="address-form-error">
          {{ getFieldError('phone') }}
        </p>
      </div>

      <div class="address-form-field" :class="{ 'has-error': getFieldError('email') }">
        <label class="field-label" for="address-email">
          Email address <span class="address-form-optional">Optional</span>
        </label>
        <input
          id="address-email"
          v-model="form.email"
          class="form-input"
          type="email"
          autocomplete="email"
          placeholder="name@example.com"
          :aria-invalid="Boolean(getFieldError('email'))"
          aria-describedby="address-email-error"
          @blur="markFieldTouched('email')"
        />
        <p v-if="getFieldError('email')" id="address-email-error" class="address-form-error">
          {{ getFieldError('email') }}
        </p>
      </div>
    </section>

    <section class="address-form-section" aria-labelledby="address-details-title">
      <h2 id="address-details-title">Address details</h2>

      <button
        class="address-form-location"
        :class="{ 'is-captured': hasCapturedLocation, 'is-detecting': isDetectingAddressLocation }"
        type="button"
        :disabled="isDetectingAddressLocation"
        @click="$emit('use-current-location')"
      >
        <span class="address-form-location-icon" aria-hidden="true">
          <span v-if="isDetectingAddressLocation" class="address-form-spinner"></span>
          <svg v-else-if="hasCapturedLocation" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5 12.5l4.5 4.5L19 7.5" />
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="3.5" />
            <path d="M12 2v3M12 19v3M2 12h3M19 12h3" />
          </svg>
        </span>
        <span class="address-form-location-text" aria-live="polite">
          <strong>
            {{ isDetectingAddressLocation ? 'Detecting your location...' : (hasCapturedLocation ? 'Location captured' : 'Use current location') }}
          </strong>
          <small>
            {{ hasCapturedLocation && !isDetectingAddressLocation ? (form.area || 'Tap to detect again') : 'Fills in your street and building for you' }}
          </small>
        </span>
      </button>
      <p v-if="addressLocationError" class="form-message error-message profile-address-location-message">
        {{ addressLocationError }}
      </p>
      <p v-else-if="isAddressLocationEditedManually" class="address-form-hint">
        Address edited, so your manual details will be saved.
      </p>

      <div class="address-form-field" :class="{ 'has-error': getFieldError('apartmentOfficeName') }">
        <label class="field-label" for="address-apartment-office-name">
          {{ apartmentOfficeNameLabel }}
        </label>
        <input
          id="address-apartment-office-name"
          v-model="form.apartmentOfficeName"
          class="form-input"
          type="text"
          :placeholder="apartmentOfficeNamePlaceholder"
          :aria-invalid="Boolean(getFieldError('apartmentOfficeName'))"
          aria-describedby="address-apartment-office-name-error"
          @blur="markFieldTouched('apartmentOfficeName')"
        />
        <p v-if="getFieldError('apartmentOfficeName')" id="address-apartment-office-name-error" class="address-form-error">
          {{ getFieldError('apartmentOfficeName') }}
        </p>
      </div>

      <div class="address-form-field" :class="{ 'has-error': getFieldError('apartmentOfficeNo') }">
        <label class="field-label" for="address-apartment-office-no">
          {{ apartmentOfficeNoLabel }}
        </label>
        <input
          id="address-apartment-office-no"
          v-model="form.apartmentOfficeNo"
          class="form-input"
          type="text"
          :placeholder="apartmentOfficeNoPlaceholder"
          :aria-invalid="Boolean(getFieldError('apartmentOfficeNo'))"
          aria-describedby="address-apartment-office-no-error"
          @blur="markFieldTouched('apartmentOfficeNo')"
        />
        <p v-if="getFieldError('apartmentOfficeNo')" id="address-apartment-office-no-error" class="address-form-error">
          {{ getFieldError('apartmentOfficeNo') }}
        </p>
      </div>

      <div class="address-form-field" :class="{ 'has-error': getFieldError('building') }">
        <label class="field-label" for="address-building">Building / villa</label>
        <input
          id="address-building"
          v-model="form.building"
          class="form-input"
          type="text"
          placeholder="Building, floor, apartment or villa number"
          :aria-invalid="Boolean(getFieldError('building'))"
          aria-describedby="address-building-error"
          @blur="markFieldTouched('building')"
          @input="$emit('edited')"
        />
        <p v-if="getFieldError('building')" id="address-building-error" class="address-form-error">
          {{ getFieldError('building') }}
        </p>
      </div>

      <div class="address-form-field">
        <label class="field-label" for="address-street">
          Street <span class="address-form-optional">Optional</span>
        </label>
        <input
          id="address-street"
          v-model="form.street"
          class="form-input"
          type="text"
          placeholder="Street name"
          @input="$emit('edited')"
        />
      </div>

      <div class="address-form-field">
        <label class="field-label" for="address-landmark">
          Landmark <span class="address-form-optional">Optional</span>
        </label>
        <input
          id="address-landmark"
          v-model="form.landmark"
          class="form-input"
          type="text"
          placeholder="Nearby landmark"
          @input="$emit('edited')"
        />
      </div>

      <div class="address-form-field">
        <label class="field-label" for="address-emirate">
          Emirate <span class="address-form-optional">Optional</span>
        </label>
        <input
          id="address-emirate"
          v-model="form.emirate"
          class="form-input"
          type="text"
          placeholder="Dubai, Abu Dhabi, Sharjah"
          @input="$emit('edited')"
        />
      </div>
    </section>

    <label class="address-form-default" :class="{ 'is-on': form.isDefault }">
      <span>
        <strong>Use as default</strong>
        <small>Select this address automatically at checkout</small>
      </span>
      <input v-model="form.isDefault" type="checkbox" role="switch" />
      <span class="address-form-switch" aria-hidden="true"></span>
    </label>

    <div class="profile-address-form-actions">
      <button class="login-button" type="submit">
        {{ isEditing ? 'Update address' : 'Save address' }}
      </button>
      <button class="profile-address-cancel-button" type="button" @click="$emit('cancel')">
        Cancel
      </button>
    </div>
  </form>
</template>
