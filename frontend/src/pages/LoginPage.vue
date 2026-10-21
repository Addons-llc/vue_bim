<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { googleLogin, logout, reloadToLogin, requestLinkPhoneOtp, requestPhoneOtp } from '../api/authApi'
import { prepareGoogleSignIn, requestGoogleAccessToken } from '../api/googleIdentity'
import { setCurrentUser } from '../data/authStore'

const phoneNumber = ref('')
const errorMessage = ref('')
const successMessage = ref('')
const isSubmitting = ref(false)
const appBase = import.meta.env.BASE_URL
const router = useRouter()
const route = useRoute()
// Signed in (e.g. with Google) but no verified phone yet: the number is
// attached to the current account instead of signing in with it.
const isLinkMode = computed(() => route.name === 'verify-phone')
const AUTO_PROMPT_LOCATION_KEY = 'buyInMinutesPromptLocationOnHome'
const isGoogleSubmitting = ref(false)

const normalizedPhoneNumber = computed(() => {
  const digits = phoneNumber.value.replace(/\D/g, '')
  let localNumber = digits

  if (localNumber.startsWith('00971')) {
    localNumber = localNumber.slice(5)
  } else if (localNumber.startsWith('971')) {
    localNumber = localNumber.slice(3)
  }

  localNumber = localNumber.replace(/^0+/, '')

  return `+971${localNumber}`
})

async function handlePhoneSignIn() {
  errorMessage.value = ''
  successMessage.value = ''
  isSubmitting.value = true

  try {
    console.log('Phone OTP request payload', {
      phoneNumber: normalizedPhoneNumber.value,
    })
    const response = isLinkMode.value
      ? await requestLinkPhoneOtp(normalizedPhoneNumber.value)
      : await requestPhoneOtp(normalizedPhoneNumber.value)
    console.log('Phone OTP request response', response)

    if (!response?.message?.success) {
      throw new Error(response?.message?.message || 'Unable to send OTP.')
    }

    successMessage.value = response.message.message || 'OTP sent successfully.'
    await router.push({
      name: 'login-otp',
      query: {
        phone: normalizedPhoneNumber.value,
        flow: response?.message?.auth_flow_token || '',
        mode: response?.message?.auth_mode || '',
        ...(isLinkMode.value ? { purpose: 'link' } : {}),
      },
    })
  } catch (error) {
    console.error('Phone OTP request failed', error)
    errorMessage.value = error.message
  } finally {
    isSubmitting.value = false
  }
}

async function handleGoogleSignIn() {
  if (isGoogleSubmitting.value) {
    return
  }

  errorMessage.value = ''
  successMessage.value = ''
  isGoogleSubmitting.value = true

  try {
    const accessToken = await requestGoogleAccessToken()
    const response = await googleLogin(accessToken)
    const result = response?.message

    if (!result?.success) {
      throw new Error(result?.message || 'Unable to sign in with Google.')
    }

    successMessage.value = 'Signed in successfully.'
    setCurrentUser(result.user || null)

    if (result.needs_phone || !result.user?.mobile_no) {
      await router.push({ name: 'verify-phone' })
      return
    }

    sessionStorage.setItem(AUTO_PROMPT_LOCATION_KEY, '1')
    await router.push({ name: 'home' })
  } catch (error) {
    if (!error.cancelled) {
      console.error('Google sign-in failed', error)
      errorMessage.value = error.message
    }
  } finally {
    isGoogleSubmitting.value = false
  }
}

onMounted(() => {
  prepareGoogleSignIn().catch((error) => console.error('Google sign-in setup failed', error))
})

// The same component instance can serve both routes.
watch(isLinkMode, () => {
  errorMessage.value = ''
  successMessage.value = ''
})

async function useDifferentAccount() {
  try {
    await logout()
  } catch (error) {
    console.error('Logout failed', error)
  }

  reloadToLogin()
}

function handleProviderSignIn(providerName) {
  errorMessage.value = ''

  successMessage.value = `${providerName} sign-in is coming soon. Please use your mobile number for now.`
}

function skipSignIn() {
  sessionStorage.setItem(AUTO_PROMPT_LOCATION_KEY, '1')
  router.push({ name: 'home' })
}
</script>

<template>
  <main class="auth-page signin-page">
    <section class="signin-shell">
      <header class="signin-hero">
        <a class="signin-brand" :href="appBase" aria-label="Buy In Minutes home">
          <img class="signin-logo" :src="`${appBase}bim.jpeg`" alt="" />
          <span class="signin-brand-name">Buy In Minutes</span>
        </a>
        <p class="signin-tagline">Groceries and essentials, delivered in minutes.</p>
        <ul class="signin-perks" aria-hidden="true">
          <li>Fast delivery</li>
          <li>Trusted stores</li>
          <li>Secure checkout</li>
        </ul>
      </header>

      <section class="signin-card">
        <div class="signin-heading">
          <template v-if="isLinkMode">
            <h1>Verify your mobile number</h1>
            <p>Add your mobile number for delivery updates. We'll send you a one-time code.</p>
          </template>
          <template v-else>
            <h1>Sign in</h1>
            <p>Enter your mobile number and we'll send you a one-time code.</p>
          </template>
        </div>

        <form class="signin-form" @submit.prevent="handlePhoneSignIn">
          <label class="signin-label" for="phone">Mobile number</label>
          <div class="signin-phone">
            <span class="signin-country">
              <span class="signin-flag" aria-hidden="true">🇦🇪</span>
              +971
            </span>
            <input
              id="phone"
              v-model="phoneNumber"
              class="signin-input"
              type="tel"
              inputmode="tel"
              autocomplete="tel"
              placeholder="50 123 4567"
              required
            />
          </div>

          <button class="signin-submit" type="submit" :disabled="isSubmitting">
            <span>{{ isSubmitting ? 'Sending OTP...' : 'Continue' }}</span>
            <svg
              v-if="!isSubmitting"
              aria-hidden="true"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.4"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M5 12h14" />
              <path d="M13 6l6 6-6 6" />
            </svg>
          </button>
        </form>

        <p v-if="errorMessage" class="signin-message is-error">
          {{ errorMessage }}
        </p>

        <p v-if="successMessage" class="signin-message is-success">
          {{ successMessage }}
        </p>

        <template v-if="isLinkMode">
          <button class="signin-skip" type="button" @click="useDifferentAccount">
            Use a different account
          </button>
        </template>

        <template v-else>
          <div class="signin-divider"><span>or continue with</span></div>

          <div class="signin-social">

            <button
              class="signin-social-button is-google"
              type="button"
              :disabled="isGoogleSubmitting"
              @click="handleGoogleSignIn"
            >
              <svg aria-hidden="true" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M23.52 12.27c0-.85-.08-1.67-.22-2.45H12v4.64h6.46a5.52 5.52 0 0 1-2.4 3.62v3h3.88c2.27-2.09 3.58-5.17 3.58-8.81z" />
                <path fill="#34A853" d="M12 24c3.24 0 5.96-1.07 7.94-2.9l-3.88-3.02c-1.07.72-2.45 1.15-4.06 1.15-3.13 0-5.78-2.11-6.72-4.95H1.27v3.11A12 12 0 0 0 12 24z" />
                <path fill="#FBBC05" d="M5.28 14.28a7.2 7.2 0 0 1 0-4.56V6.61H1.27a12 12 0 0 0 0 10.78l4.01-3.11z" />
                <path fill="#EA4335" d="M12 4.77c1.76 0 3.34.61 4.59 1.8l3.44-3.44A11.97 11.97 0 0 0 1.27 6.61l4.01 3.11C6.22 6.88 8.87 4.77 12 4.77z" />
              </svg>
              <span>{{ isGoogleSubmitting ? 'Signing in...' : 'Continue with Google' }}</span>
            </button>

            <button class="signin-social-button is-apple" type="button" @click="handleProviderSignIn('Apple')">
              <svg aria-hidden="true" viewBox="0 0 24 24" fill="currentColor">
                <path d="M16.37 12.6c-.02-2.3 1.88-3.4 1.96-3.46-1.07-1.56-2.73-1.78-3.32-1.8-1.41-.14-2.76.83-3.47.83-.72 0-1.82-.81-2.99-.79-1.54.02-2.96.9-3.75 2.27-1.6 2.78-.41 6.89 1.15 9.14.76 1.1 1.67 2.34 2.86 2.3 1.15-.05 1.58-.74 2.97-.74 1.38 0 1.77.74 2.98.72 1.23-.02 2.01-1.12 2.76-2.23.87-1.28 1.23-2.52 1.25-2.58-.03-.01-2.39-.92-2.4-3.66zM14.1 5.86c.63-.77 1.06-1.83.94-2.89-.91.04-2.01.61-2.66 1.37-.58.67-1.09 1.75-.96 2.79 1.02.08 2.05-.52 2.68-1.27z" />
              </svg>
              <span>Continue with Apple</span>
            </button>
          </div>

          <button class="signin-skip" type="button" @click="skipSignIn">
            Skip for now and browse
          </button>
        </template>

        <p class="signin-note">
          <svg
            aria-hidden="true"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <rect x="5" y="11" width="14" height="10" rx="2" />
            <path d="M8 11V7a4 4 0 0 1 8 0v4" />
          </svg>
          Your number is only used to verify your account.
        </p>
      </section>
    </section>
  </main>
</template>
