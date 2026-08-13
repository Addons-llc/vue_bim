<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { currentUser } from '../../data/authStore'
import { cartItemCount } from '../../data/cartStore'

const emit = defineEmits(['login'])

const route = useRoute()
const router = useRouter()

const isAuthenticated = computed(() => Boolean(currentUser.value))
const isHomeActive = computed(() => route.name === 'home')
const isCategoriesActive = computed(() => ['categories', 'category-details'].includes(route.name))
const isCartActive = computed(() => route.name === 'cart')
const isAccountActive = computed(() => route.name === 'profile')

function goToAccount() {
  if (!isAuthenticated.value) {
    emit('login')
    return
  }

  router.push({ name: 'profile' })
}
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
      :class="{ 'is-active': isCartActive }"
      :to="{ name: 'cart' }"
    >
      <span class="mobile-nav-icon-wrap">
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
          <circle cx="8" cy="21" r="1" />
          <circle cx="19" cy="21" r="1" />
          <path d="M2 2h3l3 13h10l3-8H7" />
        </svg>
        <span
          v-if="cartItemCount"
          class="mobile-nav-badge"
          :aria-label="`${cartItemCount} items in cart`"
        >
          {{ cartItemCount }}
        </span>
      </span>
      <span class="mobile-nav-label">Cart</span>
    </RouterLink>

    <button
      class="mobile-nav-item"
      type="button"
      :class="{ 'is-active': isAccountActive }"
      @click="goToAccount"
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
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21c1.6-4 5-6 8-6s6.4 2 8 6" />
      </svg>
      <span class="mobile-nav-label">Account</span>
    </button>
  </nav>
</template>
