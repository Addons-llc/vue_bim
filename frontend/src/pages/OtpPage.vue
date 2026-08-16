<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { requestPhoneOtp, verifyPhoneOtp } from '../api/authApi'
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
  if (!phoneNumber.value) {
    router.replace({ name: 'login' })
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
    })
    const response = await verifyPhoneOtp(phoneNumber.value, otp.value)
    console.log('Phone OTP verify response', response)
    const otpResult = getOtpResult(response)

    if (!otpResult.success) {
      throw new Error(otpResult.message || 'Unable to verify OTP.')
    }

    const profileCompleted = getProfileCompletedFromResponse(response)

    successMessage.value = 'Signed in successfully.'

    if (profileCompleted) {
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
    const response = await requestPhoneOtp(phoneNumber.value)
    console.log('Phone OTP resend response', response)
    resetOtpDigits()
    successMessage.value = 'OTP sent to your phone number.'
    startResendTimer()
  } catch (error) {
    console.error('Phone OTP resend failed', error)
    errorMessage.value = error.message
  } finally {
    isSubmitting.value = false
  }
}

function changePhoneNumber() {
  router.push({ name: 'login' })
}
</script>

<template>
  <main class="auth-page">
    <section class="login-panel">
      <a class="auth-brand" :href="appBase" aria-label="Buy In Minutes home">
        <img class="brand-logo" :src="`${appBase}bim.jpeg`" alt="" />
        <span class="brand-name">BIM</span>
      </a>

      <div class="login-heading otp-heading">
        <p class="section-label">Verification</p>
        <h1>Enter OTP</h1>
        <p class="login-copy">
          We've sent a 6-digit code to
          <strong>{{ phoneNumber }}</strong>
        </p>
        <button class="otp-change-number" type="button" @click="changePhoneNumber">
          Not your number? Change
        </button>
      </div>

      <section class="auth-section otp-section">
        <form class="login-form otp-form" @submit.prevent="handleOtpVerification">
          <div class="otp-boxes" role="group" aria-label="Verification code">
            <input
              v-for="(digit, index) in otpDigits"
              :id="`otp-${index}`"
              :key="index"
              :ref="(el) => setDigitInputRef(el, index)"
              class="otp-box"
              :class="{ 'is-filled': digit }"
              type="text"
              inputmode="numeric"
              autocomplete="one-time-code"
              maxlength="1"
              :value="digit"
              @input="handleDigitInput(index, $event)"
              @keydown="handleDigitKeydown(index, $event)"
              @paste="handleDigitPaste(index, $event)"
            />
          </div>

          <button class="login-button" type="submit" :disabled="isSubmitting || otp.length !== OTP_LENGTH">
            {{ isSubmitting ? 'Verifying...' : 'Verify and sign in' }}
          </button>

          <button
            class="resend-button"
            type="button"
            :disabled="!canResendOtp"
            @click="resendOtp"
          >
            {{
              resendSecondsRemaining
                ? `Resend OTP in ${resendSecondsRemaining}s`
                : 'Resend OTP'
            }}
          </button>
        </form>
      </section>

      <p v-if="successMessage" class="form-message success-message">
        {{ successMessage }}
      </p>
      <p v-if="errorMessage" class="form-message error-message">
        {{ errorMessage }}
      </p>
    </section>
  </main>
</template>
