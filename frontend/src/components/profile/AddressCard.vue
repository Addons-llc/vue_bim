<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  address: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['set-default', 'edit', 'delete'])

const isConfirmingDelete = ref(false)
const isExpanded = ref(false)

const labelKind = computed(() => {
  const label = String(props.address.label || '').toLowerCase()

  if (label === 'home') {
    return 'home'
  }

  return label === 'office' ? 'office' : 'other'
})

const summaryLine = computed(() =>
  [
    props.address.apartmentOfficeNo,
    props.address.apartmentOfficeName,
    props.address.building,
    props.address.street,
    props.address.area,
    props.address.emirate,
  ]
    .filter(Boolean)
    .join(', '),
)

function confirmDelete() {
  isConfirmingDelete.value = false
  emit('delete', props.address.id)
}
</script>

<template>
  <article
    class="account-address-card"
    :class="{ 'is-default': address.isDefault, 'is-expanded': isExpanded }"
  >
    <button
      class="account-address-main"
      type="button"
      :aria-expanded="isExpanded"
      @click="isExpanded = !isExpanded"
    >
      <span class="account-address-icon" :class="`is-${labelKind}`" aria-hidden="true">
        <svg v-if="labelKind === 'home'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 11l9-8 9 8" />
          <path d="M5 10v10h14V10" />
        </svg>
        <svg v-else-if="labelKind === 'office'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="4" y="3" width="16" height="18" rx="2" />
          <path d="M9 7h1M14 7h1M9 11h1M14 11h1M10 21v-4h4v4" />
        </svg>
        <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 21s-7-6.2-7-12a7 7 0 0 1 14 0c0 5.8-7 12-7 12Z" />
          <circle cx="12" cy="9" r="2.5" />
        </svg>
      </span>
      <span class="account-address-text">
        <span class="account-address-title">
          <strong>{{ address.label }}</strong>
          <span v-if="address.isDefault" class="account-address-badge">Default</span>
        </span>
        <span class="account-address-summary">{{ summaryLine || 'No address details' }}</span>
      </span>
      <svg class="account-chevron" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
        <path d="m6 9 6 6 6-6" />
      </svg>
    </button>

    <div class="account-collapse" :class="{ 'is-open': isExpanded }">
      <div class="account-collapse-inner">
        <dl class="account-address-details">
          <div>
            <dt>Contact</dt>
            <dd>{{ address.contactName }} · {{ address.phone }}</dd>
          </div>
          <div v-if="address.email">
            <dt>Email</dt>
            <dd>{{ address.email }}</dd>
          </div>
          <div v-if="address.apartmentOfficeName">
            <dt>{{ address.label === 'Office' ? 'Office name' : 'Apartment name' }}</dt>
            <dd>{{ address.apartmentOfficeName }}</dd>
          </div>
          <div v-if="address.apartmentOfficeNo">
            <dt>{{ address.label === 'Office' ? 'Office no' : 'Apartment no' }}</dt>
            <dd>{{ address.apartmentOfficeNo }}</dd>
          </div>
          <div v-if="address.building">
            <dt>Building / villa</dt>
            <dd>{{ address.building }}</dd>
          </div>
          <div v-if="address.street">
            <dt>Street</dt>
            <dd>{{ address.street }}</dd>
          </div>
          <div v-if="address.emirate">
            <dt>Emirate</dt>
            <dd>{{ address.emirate }}</dd>
          </div>
          <div v-if="address.landmark">
            <dt>Landmark</dt>
            <dd>{{ address.landmark }}</dd>
          </div>
        </dl>

        <div v-if="isConfirmingDelete" class="account-address-confirm" role="alert">
          <span>Delete this address?</span>
          <button type="button" class="is-ghost" @click="isConfirmingDelete = false">Keep</button>
          <button type="button" class="is-danger" @click="confirmDelete">Delete</button>
        </div>

        <div v-else class="account-address-actions">
          <button
            v-if="!address.isDefault"
            type="button"
            @click="emit('set-default', address.id)"
          >
            Set as default
          </button>
          <button type="button" @click="emit('edit', address)">Edit</button>
          <button type="button" class="is-danger-text" @click="isConfirmingDelete = true">Delete</button>
        </div>
      </div>
    </div>
  </article>
</template>
