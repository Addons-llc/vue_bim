<script setup>
import { ref } from 'vue'
import { requestPhoneOtp, signInWithProvider } from '../api/authApi'

const phoneNumber = ref('')
const errorMessage = ref('')
const successMessage = ref('')
const isSubmitting = ref(false)
const appBase = import.meta.env.BASE_URL

async function handlePhoneSignIn() {
  errorMessage.value = ''
  successMessage.value = ''
  isSubmitting.value = true

  try {
    await requestPhoneOtp(`+971${phoneNumber.value}`)
    successMessage.value = 'OTP sent to your phone number.'
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    isSubmitting.value = false
  }
}

async function handleProviderSignIn(provider) {
  errorMessage.value = ''
  successMessage.value = ''

  try {
    await signInWithProvider(provider.toLowerCase())
  } catch (error) {
    errorMessage.value = error.message
  }
}
</script>

<template>
  <main class="auth-page">
    <section class="login-panel">
      <a class="auth-brand" :href="appBase" aria-label="Buy In Minutes home">
        <img class="brand-logo" :src="`${appBase}bim.jpeg`" alt="" />
        <span class="brand-name">BUY IN MINUTES</span>
      </a>

      <div class="login-heading">
        <p class="section-label">Account access</p>
        <h1>Sign in</h1>
        <p class="login-copy">Enter your mobile number to continue shopping.</p>
      </div>

      <form class="login-form" @submit.prevent="handlePhoneSignIn">
        <label class="field-label" for="phone">Phone number</label>
        <div class="phone-input-row">
          <span class="country-code">+971</span>
          <input
            id="phone"
            v-model="phoneNumber"
            class="form-input phone-input"
            type="tel"
            placeholder="50 123 4567"
          />
        </div>

        <button class="login-button" type="submit" :disabled="isSubmitting">
          {{ isSubmitting ? 'Sending OTP...' : 'Continue' }}
        </button>
      </form>

      <p v-if="successMessage" class="form-message success-message">
        {{ successMessage }}
      </p>
      <p v-if="errorMessage" class="form-message error-message">
        {{ errorMessage }}
      </p>

      <div class="auth-divider">
        <span></span>
        <p>or sign in with</p>
        <span></span>
      </div>

      <div class="provider-actions">
        <button
          class="provider-button"
          type="button"
          @click="handleProviderSignIn('Google')"
        >
          <span class="provider-icon google-icon" aria-hidden="true">G</span>
          <span>Google</span>
        </button>

        <button
          class="provider-button"
          type="button"
          @click="handleProviderSignIn('Apple')"
        >
          <span class="provider-icon apple-icon" aria-hidden="true"></span>
          <span>Apple</span>
        </button>
      </div>
    </section>
  </main>
</template>
