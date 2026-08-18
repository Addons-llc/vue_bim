import { apiRequest, clearStoredCsrfToken } from './http'
import { clearCurrentUser } from '../data/authStore'

export const AUTH_TOKEN_STORAGE_KEY = 'authToken'
export const AUTH_FLOW_TOKEN_STORAGE_KEY = 'authFlowToken'

function storeAuthToken(response) {
  const token = response?.message?.session_token || response?.message?.token || ''

  if (token) {
    localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, token)
  }
}

function storeAuthFlowToken(response) {
  const flowToken = response?.message?.auth_flow_token || ''

  if (flowToken) {
    localStorage.setItem(AUTH_FLOW_TOKEN_STORAGE_KEY, flowToken)
  }
}

export function hasPersistedPhoneAuthState() {
  return Boolean(
    localStorage.getItem(AUTH_TOKEN_STORAGE_KEY)
    || localStorage.getItem(AUTH_FLOW_TOKEN_STORAGE_KEY),
  )
}

export function requestPhoneOtp(phoneNumber) {
  const params = new URLSearchParams({ phone_number: phoneNumber })

  return apiRequest(`/method/buy_in_minutes.auth.request_phone_otp?${params.toString()}`)
    .then((response) => {
      if (response?.message?.success) {
        storeAuthFlowToken(response)
      }

      return response
    })
}

export async function verifyPhoneOtp(phoneNumber, otp, authFlowToken = '') {
  const response = await apiRequest('/method/buy_in_minutes.auth.verify_phone_otp', {
    method: 'POST',
    body: JSON.stringify({ phone_number: phoneNumber, otp, auth_flow_token: authFlowToken }),
  })

  if (response?.message?.success) {
    storeAuthToken(response)
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
    storeAuthToken(response)
    clearStoredCsrfToken()
  }

  return response
}

export async function restoreLoginSession() {
  const sessionToken = localStorage.getItem(AUTH_TOKEN_STORAGE_KEY)

  if (!sessionToken) {
    return null
  }

  const response = await apiRequest('/method/buy_in_minutes.auth.restore_login_session', {
    method: 'POST',
    body: JSON.stringify({
      session_token: sessionToken,
    }),
  })

  if (response?.message?.success) {
    storeAuthToken(response)
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

  localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY)
  localStorage.removeItem(AUTH_FLOW_TOKEN_STORAGE_KEY)
  clearStoredCsrfToken()
  clearCurrentUser()
  return request
}
