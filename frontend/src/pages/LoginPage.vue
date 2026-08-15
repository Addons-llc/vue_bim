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
  <main class="auth-page">
    <section class="login-panel">
      <a class="auth-brand" :href="appBase" aria-label="Buy In Minutes home">
        <img class="brand-logo" :src="`${appBase}bim.jpeg`" alt="" />
        <span class="brand-name">BIM</span>
      </a>

      <div class="login-heading">
        <p class="section-label">Account access</p>
        <h1>Sign in</h1>
        <p class="login-copy">Enter your mobile number to continue shopping.</p>
      </div>

      <section class="auth-section">
        <form class="login-form" @submit.prevent="handlePhoneSignIn">
          <label class="field-label" for="phone">Phone number</label>
          <div class="phone-input-row">
            <span class="country-code">+971</span>
            <input
              id="phone"
              v-model="phoneNumber"
              class="form-input phone-input"
              type="tel"
              inputmode="tel"
              autocomplete="tel"
              placeholder="50 123 4567"
              required
            />
          </div>

          <button class="login-button" type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? 'Sending OTP...' : 'Continue' }}
          </button>
        </form>
      </section>

      <p v-if="successMessage" class="form-message success-message">
        {{ successMessage }}
      </p>
      <p v-if="errorMessage" class="form-message error-message">
        {{ errorMessage }}
      </p>

      <button class="skip-signin-button" type="button" @click="skipSignIn">
        Skip for now
      </button>
    </section>
  </main>
</template>
