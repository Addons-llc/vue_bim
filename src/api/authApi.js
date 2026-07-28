import { apiRequest } from './http'

export function requestPhoneOtp(phoneNumber) {
  return apiRequest('/auth/phone/request-otp', {
    method: 'POST',
    body: JSON.stringify({ phoneNumber }),
  })
}

export function verifyPhoneOtp(phoneNumber, otp) {
  return apiRequest('/auth/phone/verify-otp', {
    method: 'POST',
    body: JSON.stringify({ phoneNumber, otp }),
  })
}

export function signInWithProvider(provider) {
  return apiRequest(`/auth/${provider}/start`)
}

export function logout() {
  localStorage.removeItem('authToken')
}
