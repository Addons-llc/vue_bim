import { apiRequest } from './http'
import { clearCurrentUser } from '../data/authStore'

export function requestPhoneOtp(phoneNumber) {
  const params = new URLSearchParams({ phone_number: phoneNumber })

  return apiRequest(`/method/buy_in_minutes.auth.request_phone_otp?${params.toString()}`)
}

export function verifyPhoneOtp(phoneNumber, otp) {
  return apiRequest('/method/buy_in_minutes.auth.verify_phone_otp', {
    method: 'POST',
    body: JSON.stringify({ phone_number: phoneNumber, otp }),
  })
}

export function createWebsiteUser({ email, fullName, phoneNumber, profileToken }) {
  return apiRequest('/method/buy_in_minutes.auth.complete_phone_profile', {
    method: 'POST',
    body: JSON.stringify({
      email: email.trim(),
      full_name: fullName.trim(),
      phone_number: phoneNumber,
      profile_token: profileToken,
    }),
  })
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
  clearCurrentUser()
  return request
}
