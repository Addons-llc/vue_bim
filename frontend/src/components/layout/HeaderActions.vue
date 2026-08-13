<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { currentUser } from '../../data/authStore'
import { cartItemCount } from '../../data/cartStore'
import { wishlistItemCount } from '../../data/wishlistStore'

const emit = defineEmits(['cart', 'login', 'logout', 'wishlist'])

const route = useRoute()
const isAccountMenuOpen = ref(false)
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

function handleAccountAction() {
  if (isAuthenticated.value) {
    isAccountMenuOpen.value = !isAccountMenuOpen.value
    return
  }

  emit('login')
}

function closeAccountMenu() {
  isAccountMenuOpen.value = false
}

function handleLogout() {
  closeAccountMenu()
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
      class="header-action-button cart-link"
      :class="{ 'has-items': cartItemCount }"
      type="button"
      @click="emit('cart')"
    >
      <svg
        class="action-svg"
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
      <span class="cart-count" :aria-label="`${cartItemCount} items in cart`">
        <span class="cart-count-number">{{ cartItemCount }}</span>
        <span class="cart-count-label"> items</span>
      </span>
    </button>

    <div class="account-menu-wrap">
      <button
        class="logout-button"
        type="button"
        aria-haspopup="menu"
        :aria-expanded="isAuthenticated ? isAccountMenuOpen : undefined"
        @click="handleAccountAction"
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
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
          <path d="M16 17l5-5-5-5" />
          <path d="M21 12H9" />
        </svg>
        <span>{{ accountLabel }}</span>
      </button>

      <div v-if="isAuthenticated && isAccountMenuOpen" class="account-menu" role="menu">
        <RouterLink
          class="account-menu-item"
          :to="{ name: 'profile' }"
          role="menuitem"
          @click="closeAccountMenu"
        >
          View profile
        </RouterLink>
        <button
          class="account-menu-item"
          type="button"
          role="menuitem"
          @click="handleLogout"
        >
          Logout
        </button>
      </div>
    </div>
  </nav>
</template>
