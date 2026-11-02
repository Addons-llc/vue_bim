<script setup>
import { computed } from 'vue'
import explorePlaceholder from '../assets/images/explore-placeholder.svg'
import servicesPlaceholder from '../assets/images/services-placeholder.svg'

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  message: {
    type: String,
    required: true,
  },
  // 'explore' | 'services' shows only that tab's placeholder image.
  // Leave empty for the plain coming-soon text (privacy policy, terms).
  variant: {
    type: String,
    default: '',
  },
})

// To use your own artwork, replace these files in src/assets/images/.
const PLACEHOLDER_IMAGES = {
  explore: explorePlaceholder,
  services: servicesPlaceholder,
}

const placeholderImage = computed(() => PLACEHOLDER_IMAGES[props.variant] || '')
</script>

<template>
  <section v-if="placeholderImage" class="coming-soon-page is-placeholder">
    <img
      class="coming-soon-placeholder-image"
      :src="placeholderImage"
      :alt="`${title} coming soon`"
    />
  </section>

  <section v-else class="coming-soon-page">
    <h1>{{ title }}</h1>
    <p>{{ message }}</p>
    <RouterLink class="coming-soon-page-link" :to="{ name: 'home' }">Continue shopping</RouterLink>
  </section>
</template>
