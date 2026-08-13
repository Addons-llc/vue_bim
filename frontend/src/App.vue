<script setup>
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getCurrentUser, logout } from './api/authApi'
import { clearCurrentUser, setCurrentUser } from './data/authStore'
import DefaultLayout from './layouts/DefaultLayout.vue'

const route = useRoute()
const router = useRouter()

onMounted(async () => {
  try {
    const response = await getCurrentUser()
    const message = response?.message || {}

    if (message.is_authenticated) {
      setCurrentUser(message.user)
      return
    }
  } catch (error) {
    console.error('Unable to load current user session', error)
  }

  clearCurrentUser()
})

function navigateToLogin() {
  router.push({ name: 'login' })
}

async function handleLogout() {
  try {
    await logout()
  } finally {
    navigateToLogin()
  }
}

function navigateToCart() {
  router.push({ name: 'cart' })
}

function navigateToWishlist() {
  router.push({ name: 'wishlist' })
}

function navigateToHome() {
  router.push({ name: 'home' })
}

function updateProductSearch(searchText) {
  router.push({
    name: 'home',
    query: searchText ? { search: searchText } : {},
  })
}
</script>

<template>
  <RouterView v-if="route.meta.layout === 'blank'" />

  <DefaultLayout
    v-else
    @cart="navigateToCart"
    @login="navigateToLogin"
    @logout="handleLogout"
    @search="updateProductSearch"
    @wishlist="navigateToWishlist"
  >
    <RouterView v-slot="{ Component }">
      <component
        :is="Component"
        v-if="route.name === 'cart'"
        @continue-shopping="navigateToHome"
        @login="navigateToLogin"
      />
      <component :is="Component" v-else />
    </RouterView>
  </DefaultLayout>
</template>
