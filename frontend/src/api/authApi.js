import { apiRequest, clearStoredCsrfToken } from './http'
import { clearCurrentUser } from '../data/authStore'

export function requestPhoneOtp(phoneNumber) {
  const params = new URLSearchParams({ phone_number: phoneNumber })

  return apiRequest(`/method/buy_in_minutes.auth.request_phone_otp?${params.toString()}`)
}

export async function verifyPhoneOtp(phoneNumber, otp) {
  const response = await apiRequest('/method/buy_in_minutes.auth.verify_phone_otp', {
    method: 'POST',
    body: JSON.stringify({ phone_number: phoneNumber, otp }),
  })

  if (response?.message?.success) {
    clearStoredCsrfToken()
  }

  return response
}

export async function createWebsiteUser({ email, fullName, phoneNumber, profileToken }) {
  const response = await apiRequest('/method/buy_in_minutes.auth.complete_phone_profile', {
    method: 'POST',
    body: JSON.stringify({
      email: email.trim(),
      full_name: fullName.trim(),
      phone_number: phoneNumber,
      profile_token: profileToken,
    }),
  })

  if (response?.message?.success) {
    clearStoredCsrfToken()
  }

  return response
}

export function getCurrentUser() {
  return apiRequest('/method/buy_in_minutes.auth.get_current_user')
}

export function signInWithProvider(provider) {
  return apiRequest(`/auth/${provider}/start`)
}

export function logout() {
  const request = apiRequest('/method/logout', {
    method: 'POST',
  })

  localStorage.removeItem('authToken')
  clearStoredCsrfToken()
  clearCurrentUser()
  return request
}
