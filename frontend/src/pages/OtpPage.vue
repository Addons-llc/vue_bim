<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  AUTH_FLOW_TOKEN_STORAGE_KEY,
  requestLinkPhoneOtp,
  requestPhoneOtp,
  verifyLinkPhoneOtp,
  verifyPhoneOtp,
} from '../api/authApi'
import { setCurrentUser } from '../data/authStore'

const OTP_LENGTH = 6

const route = useRoute()
const router = useRouter()
const otpDigits = ref(Array(OTP_LENGTH).fill(''))
const otp = computed(() => otpDigits.value.join(''))
const errorMessage = ref('')
const successMessage = ref('')
const isSubmitting = ref(false)
const resendSecondsRemaining = ref(60)
const appBase = import.meta.env.BASE_URL
let resendTimerId = null
let digitInputEls = []

const phoneNumber = computed(() => {
  const routePhone = route.query.phone
  return Array.isArray(routePhone) ? routePhone[0] : routePhone || ''
})
const authFlowToken = computed(() => {
  const routeFlow = route.query.flow
  if (Array.isArray(routeFlow) ? routeFlow[0] : routeFlow) {
    return Array.isArray(routeFlow) ? routeFlow[0] : routeFlow || ''
  }

  return localStorage.getItem(AUTH_FLOW_TOKEN_STORAGE_KEY) || ''
})

// Adding a phone to an already signed-in account (e.g. after Google sign-in).
const isLinkMode = computed(() => route.query.purpose === 'link')

const formattedPhoneNumber = computed(() => {
  const match = phoneNumber.value.match(/^\+971(\d{2})(\d{3})(\d{4})$/)
  return match ? `+971 ${match[1]} ${match[2]} ${match[3]}` : phoneNumber.value
})
const resendCountdown = computed(() => {
  const seconds = resendSecondsRemaining.value
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`
})
const submitLabel = computed(() => {
  if (isSubmitting.value) {
    return 'Verifying...'
  }

  return isLinkMode.value ? 'Verify number' : 'Verify and continue'
})

const canResendOtp = computed(() => resendSecondsRemaining.value === 0 && !isSubmitting.value)
const AUTO_PROMPT_LOCATION_KEY = 'buyInMinutesPromptLocationOnHome'

function clearResendTimer() {
  if (resendTimerId) {
    clearInterval(resendTimerId)
    resendTimerId = null
  }
}

function startResendTimer() {
  clearResendTimer()
  resendSecondsRemaining.value = 60

  resendTimerId = setInterval(() => {
    resendSecondsRemaining.value -= 1

    if (resendSecondsRemaining.value <= 0) {
      resendSecondsRemaining.value = 0
      clearResendTimer()
    }
  }, 1000)
}

onMounted(() => {
  if (!phoneNumber.value || !authFlowToken.value) {
    router.replace({ name: isLinkMode.value ? 'verify-phone' : 'login' })
    return
  }

  startResendTimer()
  nextTick(() => focusDigit(0))
})

onBeforeUnmount(() => {
  clearResendTimer()
})

function setDigitInputRef(el, index) {
  if (el) {
    digitInputEls[index] = el
  }
}

function focusDigit(index) {
  digitInputEls[index]?.focus()
}

function resetOtpDigits() {
  otpDigits.value = Array(OTP_LENGTH).fill('')
  nextTick(() => focusDigit(0))
}

function distributeDigits(value, startIndex = 0) {
  const digits = value.replace(/\D/g, '').slice(0, OTP_LENGTH - startIndex).split('')

  digits.forEach((digit, offset) => {
    otpDigits.value[startIndex + offset] = digit
  })

  if (!digits.length) {
    return
  }

  const nextIndex = Math.min(startIndex + digits.length, OTP_LENGTH - 1)
  nextTick(() => focusDigit(nextIndex))

  if (otp.value.length === OTP_LENGTH) {
    handleOtpVerification()
  }
}

function handleDigitInput(index, event) {
  const rawValue = event.target.value.replace(/\D/g, '')

  if (!rawValue) {
    otpDigits.value[index] = ''
    return
  }

  if (rawValue.length > 1) {
    distributeDigits(rawValue, index)
    return
  }

  otpDigits.value[index] = rawValue

  if (index < OTP_LENGTH - 1) {
    nextTick(() => focusDigit(index + 1))
  } else {
    event.target.blur()

    if (otp.value.length === OTP_LENGTH) {
      handleOtpVerification()
    }
  }
}

function handleDigitKeydown(index, event) {
  if (event.key === 'Backspace' && !otpDigits.value[index] && index > 0) {
    focusDigit(index - 1)
    return
  }

  if (event.key === 'ArrowLeft' && index > 0) {
    event.preventDefault()
    focusDigit(index - 1)
    return
  }

  if (event.key === 'ArrowRight' && index < OTP_LENGTH - 1) {
    event.preventDefault()
    focusDigit(index + 1)
  }
}

function handleDigitPaste(index, event) {
  event.preventDefault()
  const pasted = (event.clipboardData || window.clipboardData)?.getData('text') || ''
  distributeDigits(pasted, index)
}

function getProfileCompletedFromResponse(response) {
  const message = getOtpResult(response)

  if (typeof message.needs_profile === 'boolean') {
    return !message.needs_profile
  }

  if (typeof message.profile_completed === 'boolean') {
    return message.profile_completed
  }

  if (typeof message.is_new_user === 'boolean') {
    return !message.is_new_user
  }

  if (typeof message.website_user_exists === 'boolean') {
    return message.website_user_exists
  }

  if (typeof message.user_exists === 'boolean') {
    return message.user_exists
  }

  if (typeof message.existing_user === 'boolean') {
    return message.existing_user
  }

  if (message.website_user || message.user) {
    return true
  }

  return null
}

function getOtpResult(response) {
  return response?.message && typeof response.message === 'object'
    ? response.message
    : response || {}
}

async function handleOtpVerification() {
  if (isSubmitting.value) {
    return
  }

  errorMessage.value = ''
  successMessage.value = ''
  isSubmitting.value = true

  try {
    console.log('Phone OTP verify payload', {
      phoneNumber: phoneNumber.value,
      authFlowToken: authFlowToken.value,
    })
    const response = isLinkMode.value
      ? await verifyLinkPhoneOtp(phoneNumber.value, otp.value, authFlowToken.value)
      : await verifyPhoneOtp(phoneNumber.value, otp.value, authFlowToken.value)
    console.log('Phone OTP verify response', response)
    const otpResult = getOtpResult(response)

    if (!otpResult.success) {
      throw new Error(otpResult.message || 'Unable to verify OTP.')
    }

    if (isLinkMode.value) {
      successMessage.value = 'Phone number verified.'
      setCurrentUser(otpResult.user || null)
      sessionStorage.setItem(AUTO_PROMPT_LOCATION_KEY, '1')
      await router.push({ name: 'home' })
      return
    }

    const profileCompleted = getProfileCompletedFromResponse(response)

    successMessage.value = 'Signed in successfully.'

    if (profileCompleted) {
      // Existing website user for this number: straight to the dashboard.
      setCurrentUser(otpResult.user || null)
      sessionStorage.setItem(AUTO_PROMPT_LOCATION_KEY, '1')
      await router.push({ name: 'home' })
      return
    }

    await router.push({
      name: 'complete-profile',
      query: {
        phone: phoneNumber.value,
        token: otpResult.profile_token || '',
      },
    })
  } catch (error) {
    console.error('Phone OTP verify failed', error)
    errorMessage.value = error.message
    resetOtpDigits()
  } finally {
    isSubmitting.value = false
  }
}

async function resendOtp() {
  if (!canResendOtp.value) {
    return
  }

  errorMessage.value = ''
  successMessage.value = ''
  isSubmitting.value = true

  try {
    console.log('Phone OTP resend payload', {
      phoneNumber: phoneNumber.value,
    })
    const response = isLinkMode.value
      ? await requestLinkPhoneOtp(phoneNumber.value)
      : await requestPhoneOtp(phoneNumber.value)
    console.log('Phone OTP resend response', response)
    resetOtpDigits()
    successMessage.value = 'OTP sent to your phone number.'
    if (response?.message?.auth_flow_token) {
      await router.replace({
        name: 'login-otp',
        query: {
          ...route.query,
          flow: response.message.auth_flow_token,
          mode: response?.message?.auth_mode || '',
        },
      })
    }
    startResendTimer()
  } catch (error) {
    console.error('Phone OTP resend failed', error)
    errorMessage.value = error.message
  } finally {
    isSubmitting.value = false
  }
}

function changePhoneNumber() {
  router.push({ name: isLinkMode.value ? 'verify-phone' : 'login' })
}
</script>

<template>
  <main class="auth-page signin-page">
    <section class="signin-shell">
      <header class="signin-hero is-compact">
        <a class="signin-brand" :href="appBase" aria-label="Buy In Minutes home">
          <img class="signin-logo" :src="`${appBase}bim.jpeg`" alt="" />
          <span class="signin-brand-name">Buy In Minutes</span>
        </a>
        <span class="signin-otp-badge" aria-hidden="true">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <rect x="6" y="2" width="12" height="20" rx="3" />
            <path d="M10 6h4" />
            <path d="M9.5 14.5l1.8 1.8 3.4-3.6" />
          </svg>
        </span>
      </header>

      <section class="signin-card">
        <div class="signin-heading">
          <h1>{{ isLinkMode ? 'Verify your number' : 'Enter verification code' }}</h1>
          <p>We sent a 6-digit code by SMS to</p>
        </div>

        <div class="signin-otp-number">
          <span>{{ formattedPhoneNumber }}</span>
          <button type="button" @click="changePhoneNumber">Edit</button>
        </div>

        <form class="signin-form" @submit.prevent="handleOtpVerification">
          <div
            class="signin-otp-boxes"
            :class="{ 'has-error': errorMessage }"
            role="group"
            aria-label="Verification code"
          >
            <input
              v-for="(digit, index) in otpDigits"
              :id="`otp-${index}`"
              :key="index"
              :ref="(el) => setDigitInputRef(el, index)"
              class="signin-otp-box"
              :class="{ 'is-filled': digit }"
              type="text"
              inputmode="numeric"
              autocomplete="one-time-code"
              maxlength="1"
              :aria-label="`Digit ${index + 1}`"
              :disabled="isSubmitting"
              :value="digit"
              @input="handleDigitInput(index, $event)"
              @keydown="handleDigitKeydown(index, $event)"
              @paste="handleDigitPaste(index, $event)"
            />
          </div>

          <button class="signin-submit" type="submit" :disabled="isSubmitting || otp.length !== OTP_LENGTH">
            <span>{{ submitLabel }}</span>
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

        <p v-if="errorMessage" class="signin-message is-error" role="alert">
          {{ errorMessage }}
        </p>

        <p v-if="successMessage" class="signin-message is-success" role="status">
          {{ successMessage }}
        </p>

        <div class="signin-otp-resend">
          <span>Didn't get the code?</span>
          <button v-if="resendSecondsRemaining" type="button" disabled>
            Resend in {{ resendCountdown }}
          </button>
          <button v-else type="button" :disabled="!canResendOtp" @click="resendOtp">
            Resend code
          </button>
        </div>

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
          Never share this code with anyone.
        </p>
      </section>
    </section>
  </main>
</template>
