<script setup>
import { computed } from 'vue'

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

defineEmits(['cancel', 'edited', 'submit', 'use-current-location'])

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
</script>

<template>
  <form class="profile-address-form" @submit.prevent="$emit('submit')">
    <label class="field-label" for="address-label">Address label</label>
    <select
      id="address-label"
      v-model="form.label"
      class="form-input"
      required
    >
      <option value="Home">Home</option>
      <option value="Office">Office</option>
    </select>

    <label class="field-label" for="address-contact">Contact name</label>
    <input
      id="address-contact"
      v-model="form.contactName"
      class="form-input"
      type="text"
      autocomplete="name"
      placeholder="Receiver name"
      required
      @input="$emit('edited')"
    />

    <button
      class="profile-address-location-button"
      type="button"
      :disabled="isDetectingAddressLocation"
      @click="$emit('use-current-location')"
    >
      {{ isDetectingAddressLocation ? 'Detecting location...' : 'Use current location' }}
    </button>
    <p v-if="addressLocationError" class="form-message error-message profile-address-location-message">
      {{ addressLocationError }}
    </p>

    <label class="field-label" for="address-apartment-office-name">
      {{ apartmentOfficeNameLabel }}
    </label>
    <input
      id="address-apartment-office-name"
      v-model="form.apartmentOfficeName"
      class="form-input"
      type="text"
      :placeholder="apartmentOfficeNamePlaceholder"
      required
      @input="$emit('edited')"
    />

    <label class="field-label" for="address-apartment-office-no">
      {{ apartmentOfficeNoLabel }}
    </label>
    <input
      id="address-apartment-office-no"
      v-model="form.apartmentOfficeNo"
      class="form-input"
      type="text"
      :placeholder="apartmentOfficeNoPlaceholder"
      required
      @input="$emit('edited')"
    />

    <label class="field-label" for="address-building">Building / villa</label>
    <input
      id="address-building"
      v-model="form.building"
      class="form-input"
      type="text"
      placeholder="Building, floor, apartment or villa number"
      required
      @input="$emit('edited')"
    />

    <label class="field-label" for="address-street">Street</label>
    <input
      id="address-street"
      v-model="form.street"
      class="form-input"
      type="text"
      placeholder="Street name"
      @input="$emit('edited')"
    />

    <label class="field-label" for="address-landmark">Landmark</label>
    <input
      id="address-landmark"
      v-model="form.landmark"
      class="form-input"
      type="text"
      placeholder="Nearby landmark"
      @input="$emit('edited')"
    />

    <label class="field-label" for="address-emirate">Emirate</label>
    <input
      id="address-emirate"
      v-model="form.emirate"
      class="form-input"
      type="text"
      placeholder="Dubai, Abu Dhabi, Sharjah"
      @input="$emit('edited')"
    />

    <p v-if="form.latitude && form.longitude" class="profile-address-location-note">
      Location captured for this address.
    </p>
    <p v-else-if="isAddressLocationEditedManually" class="profile-address-location-note">
      Manual address details will be saved.
    </p>

    <label class="profile-address-default">
      <input v-model="form.isDefault" type="checkbox" />
      <span>Use as default delivery address</span>
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
