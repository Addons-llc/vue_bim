<script setup>
import { onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getCurrentUser, hasPersistedPhoneAuthState, logout, reloadToLogin, restoreLoginSession } from './api/authApi'
import { resumeCheckoutSession } from './api/paymentApi'
import { clearCurrentUser, currentUser, setCurrentUser } from './data/authStore'
import DefaultLayout from './layouts/DefaultLayout.vue'
import ConsentBanner from './components/layout/ConsentBanner.vue'
import { setAnalyticsUser, trackLogin } from './analytics'

const route = useRoute()
const router = useRouter()

// GA4: link sessions to the signed-in shopper (hashed id only) and report sign-ins.
watch(
  () => currentUser.value?.name || currentUser.value?.email || '',
  (userId, previousUserId) => {
    setAnalyticsUser(userId)
    // Only a sign-in on the login screens counts; a session restored on page load does not.
    if (userId && previousUserId === '' && route.path.startsWith('/login')) {
      trackLogin()
    }
  },
  { immediate: true },
)

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
//hello

    const restoredSession = await restoreLoginSession().catch(() => null)
    const restoredUser = restoredSession?.message?.user

    if (restoredUser) {
      setCurrentUser(restoredUser)
      return
    }

    clearCurrentUser()
    return
  } catch (error) {
    console.error('Unable to load current user session', error)
  }

  if (!currentUser.value && !hasPersistedPhoneAuthState()) {
    clearCurrentUser()
  }
})

function navigateToLogin() {
  router.push({ name: 'login' })
}

async function handleLogout() {
  try {
    await logout()
  } finally {
    reloadToLogin()
  }
}

function navigateToWishlist() {
  router.push({ name: 'wishlist' })
}

function navigateToHome() {
  router.push({ name: 'home' })
}
</script>

<template>
  <ConsentBanner />
  <RouterView v-if="route.meta.layout === 'blank'" />

  <DefaultLayout
    v-else
    @login="navigateToLogin"
    @logout="handleLogout"
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
