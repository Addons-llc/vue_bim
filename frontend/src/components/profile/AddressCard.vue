<script setup>
defineProps({
  address: {
    type: Object,
    required: true,
  },
})

defineEmits(['set-default', 'edit', 'delete'])
</script>

<template>
  <article class="profile-address-card">
    <header>
      <strong>{{ address.label }}</strong>
      <span v-if="address.isDefault">Default</span>
    </header>
    <p>{{ address.contactName }} · {{ address.phone }}</p>
    <p v-if="address.email">{{ address.email }}</p>
    <p v-if="address.apartmentOfficeName">
      {{ address.label === 'Office' ? 'Office name' : 'Apartment name' }}: {{ address.apartmentOfficeName }}
    </p>
    <p v-if="address.apartmentOfficeNo">
      {{ address.label === 'Office' ? 'Office no' : 'Apartment no' }}: {{ address.apartmentOfficeNo }}
    </p>
    <p v-if="address.building">Building / villa: {{ address.building }}</p>
    <p v-if="address.street">Street: {{ address.street }}</p>
    <p v-if="address.emirate">Emirate: {{ address.emirate }}</p>
    <p v-if="address.landmark">{{ address.landmark }}</p>
    <div class="profile-address-actions">
      <button
        v-if="!address.isDefault"
        type="button"
        @click="$emit('set-default', address.id)"
      >
        Set default
      </button>
      <button type="button" @click="$emit('edit', address)">Edit</button>
      <button type="button" @click="$emit('delete', address.id)">Delete</button>
    </div>
  </article>
</template>
