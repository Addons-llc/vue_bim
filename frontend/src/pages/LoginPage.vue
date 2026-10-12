<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { requestPhoneOtp } from '../api/authApi'

const phoneNumber = ref('')
const errorMessage = ref('')
const successMessage = ref('')
const isSubmitting = ref(false)
const appBase = import.meta.env.BASE_URL
const router = useRouter()
const AUTO_PROMPT_LOCATION_KEY = 'buyInMinutesPromptLocationOnHome'

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
    const response = await requestPhoneOtp(normalizedPhoneNumber.value)
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
      },
    })
  } catch (error) {
    console.error('Phone OTP request failed', error)
    errorMessage.value = error.message
  } finally {
    isSubmitting.value = false
  }
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
          <h1>Sign in</h1>
          <p>Enter your mobile number and we'll send you a one-time code.</p>
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

        <div class="signin-divider"><span>or</span></div>

        <button class="signin-skip" type="button" @click="skipSignIn">
          Skip for now and browse
        </button>

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
