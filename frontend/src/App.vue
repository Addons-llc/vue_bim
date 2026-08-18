<script setup>
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getCurrentUser, logout } from './api/authApi'
import { resumeCheckoutSession } from './api/paymentApi'
import { clearCurrentUser, currentUser, setCurrentUser } from './data/authStore'
import DefaultLayout from './layouts/DefaultLayout.vue'

const route = useRoute()
const router = useRouter()

onMounted(async () => {
  try {
    let checkoutResumeUser = null

    // The success page restores the session itself via finalizeStripeCheckout
    // (using the Stripe session id); resuming here too would race it and can
    // spuriously log the user out if this attempt loses the race.
    if (route.name !== 'payment-success') {
      try {
        const checkoutResumeResponse = await resumeCheckoutSession()
        checkoutResumeUser = checkoutResumeResponse?.message?.user
      } catch (error) {
        console.error('Unable to resume checkout session', error)
      }
    }

    if (checkoutResumeUser) {
      setCurrentUser(checkoutResumeUser)
      return
    }

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
