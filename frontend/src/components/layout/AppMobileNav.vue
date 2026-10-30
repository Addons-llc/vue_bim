<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const isHomeActive = computed(() => route.name === 'home')
const isCategoriesActive = computed(() => ['categories', 'category-details'].includes(route.name))
const isExploreActive = computed(() => ['stores', 'store-details'].includes(route.name))
const isServicesActive = computed(() => route.name === 'services')
</script>

<template>
  <nav class="mobile-nav" aria-label="Primary">
    <RouterLink
      class="mobile-nav-item"
      :class="{ 'is-active': isHomeActive }"
      :to="{ name: 'home' }"
    >
      <svg
        class="mobile-nav-icon"
        aria-hidden="true"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M3 11l9-8 9 8" />
        <path d="M5 10v10h14V10" />
      </svg>
      <span class="mobile-nav-label">Home</span>
    </RouterLink>

    <RouterLink
      class="mobile-nav-item"
      :class="{ 'is-active': isCategoriesActive }"
      :to="{ name: 'categories' }"
    >
      <svg
        class="mobile-nav-icon"
        aria-hidden="true"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <rect x="3" y="3" width="7" height="7" rx="1.5" />
        <rect x="14" y="3" width="7" height="7" rx="1.5" />
        <rect x="3" y="14" width="7" height="7" rx="1.5" />
        <rect x="14" y="14" width="7" height="7" rx="1.5" />
      </svg>
      <span class="mobile-nav-label">Categories</span>
    </RouterLink>

    <RouterLink
      class="mobile-nav-item"
      :class="{ 'is-active': isExploreActive }"
      :to="{ name: 'stores' }"
    >
      <svg
        class="mobile-nav-icon"
        aria-hidden="true"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M9 4L3 6v14l6-2 6 2 6-2V4l-6 2-6-2z" />
        <path d="M9 4v14" />
        <path d="M15 6v14" />
      </svg>
      <span class="mobile-nav-label">Explore</span>
    </RouterLink>

    <RouterLink
      class="mobile-nav-item"
      :class="{ 'is-active': isServicesActive }"
      :to="{ name: 'services' }"
    >
      <svg
        class="mobile-nav-icon"
        aria-hidden="true"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <rect x="2" y="7" width="20" height="14" rx="2" />
        <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" />
        <path d="M2 13h20" />
      </svg>
      <span class="mobile-nav-label">Services</span>
    </RouterLink>
  </nav>
</template>
