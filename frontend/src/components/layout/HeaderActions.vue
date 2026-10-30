<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { currentUser } from '../../data/authStore'
import { wishlistItemCount } from '../../data/wishlistStore'
import AccountDrawer from './AccountDrawer.vue'

const emit = defineEmits(['login', 'logout', 'wishlist'])

const route = useRoute()
const isAccountDrawerOpen = ref(false)
const activeLanguage = ref('en')
const isAuthenticated = computed(() => Boolean(currentUser.value))
const isWishlistActive = computed(() => route.name === 'wishlist' || wishlistItemCount.value > 0)
const accountLabel = computed(() => {
  if (!currentUser.value) {
    return 'Login'
  }

  return currentUser.value.full_name || currentUser.value.email || 'Account'
})
const accountInitial = computed(() => accountLabel.value.trim().charAt(0).toUpperCase() || 'A')

function closeAccountDrawer() {
  isAccountDrawerOpen.value = false
}

function handleLogin() {
  closeAccountDrawer()
  emit('login')
}

function handleLogout() {
  closeAccountDrawer()
  emit('logout')
}

function toggleLanguage() {
  activeLanguage.value = activeLanguage.value === 'en' ? 'ar' : 'en'
  document.documentElement.lang = activeLanguage.value
  document.documentElement.dir = activeLanguage.value === 'ar' ? 'rtl' : 'ltr'
}
</script>

<template>
  <nav class="header-actions" aria-label="Account and shopping">
    <button
      class="language-toggle-button"
      type="button"
      :aria-label="activeLanguage === 'en' ? 'Switch to Arabic' : 'Switch to English'"
      @click="toggleLanguage"
    >
      {{ activeLanguage === 'en' ? 'العربية' : 'English' }}
    </button>

    <button
      class="header-action-button wishlist-link"
      :class="{ 'has-items': wishlistItemCount, 'is-active': isWishlistActive }"
      type="button"
      :aria-label="`Wishlist, ${wishlistItemCount} items`"
      :aria-current="route.name === 'wishlist' ? 'page' : undefined"
      @click="emit('wishlist')"
    >
      <span class="wishlist-icon-wrap">
        <svg
          class="wishlist-icon"
          aria-hidden="true"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path
            d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 0 0 0-7.8z"
          />
        </svg>
        <span class="wishlist-count">{{ wishlistItemCount }}</span>
      </span>
    </button>

    <button
      class="logout-button"
      type="button"
      :aria-label="`${accountLabel}, open account menu`"
      aria-haspopup="dialog"
      :aria-expanded="isAccountDrawerOpen"
      @click="isAccountDrawerOpen = true"
    >
      <span v-if="isAuthenticated" class="account-avatar" aria-hidden="true">
        <img
          v-if="currentUser?.user_image"
          :src="currentUser.user_image"
          :alt="accountLabel"
        />
        <span v-else>{{ accountInitial }}</span>
      </span>
      <svg
        v-else
        class="action-svg"
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
      <span>{{ accountLabel }}</span>
    </button>

    <AccountDrawer
      :open="isAccountDrawerOpen"
      @close="closeAccountDrawer"
      @login="handleLogin"
      @logout="handleLogout"
    />
  </nav>
</template>
