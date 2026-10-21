import { apiRequest, clearStoredCsrfToken } from './http'
import { CHECKOUT_RESUME_TOKEN_STORAGE_KEY } from './paymentApi'
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

// Attaches a phone number to the signed-in account (e.g. after Google sign-in).
export function requestLinkPhoneOtp(phoneNumber) {
  return apiRequest('/method/buy_in_minutes.auth.request_link_phone_otp', {
    method: 'POST',
    body: JSON.stringify({ phone_number: phoneNumber }),
  })
}

export async function verifyLinkPhoneOtp(phoneNumber, otp, authFlowToken) {
  const response = await apiRequest('/method/buy_in_minutes.auth.verify_link_phone_otp', {
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

// Finishes a phone sign-up with the name and email from a Google account.
export async function completeProfileWithGoogle({ accessToken, fullName, phoneNumber, profileToken }) {
  const response = await apiRequest('/method/buy_in_minutes.auth.complete_phone_profile_with_google', {
    method: 'POST',
    body: JSON.stringify({
      access_token: accessToken,
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

let restoreLoginSessionRequest = null

// Each restore token is single-use (the server issues a fresh one), so
// callers that start at the same time — App.vue and the cart/orders pages on
// load — must share one request; a second call would present a spent token.
export function restoreLoginSession() {
  if (!restoreLoginSessionRequest) {
    restoreLoginSessionRequest = requestLoginSessionRestore().finally(() => {
      restoreLoginSessionRequest = null
    })
  }

  return restoreLoginSessionRequest
}

async function requestLoginSessionRestore() {
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

export async function googleLogin(accessToken) {
  const response = await apiRequest('/method/buy_in_minutes.auth.google_login', {
    method: 'POST',
    body: JSON.stringify({ access_token: accessToken }),
  })

  if (response?.message?.success) {
    storeAuthToken(response)
    clearStoredCsrfToken()
  }

  return response
}

// Session and account data only. Cart, wishlist, saved addresses and the
// delivery location stay: they live only in this browser, so clearing them
// would lose them for good.
function clearLocalCredentials() {
  localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY)
  localStorage.removeItem(AUTH_FLOW_TOKEN_STORAGE_KEY)
  sessionStorage.removeItem(CHECKOUT_RESUME_TOKEN_STORAGE_KEY)
  sessionStorage.removeItem('buyInMinutesLastCodOrderItems')
  clearStoredCsrfToken()
  clearCurrentUser()
}

export async function logout() {
  const sessionToken = localStorage.getItem(AUTH_TOKEN_STORAGE_KEY)

  try {
    // Revoke the 30-day restore token too, or it could sign this user in again.
    if (sessionToken) {
      await apiRequest('/method/buy_in_minutes.auth.revoke_login_session', {
        method: 'POST',
        body: JSON.stringify({ session_token: sessionToken }),
      }).catch((error) => console.error('Session token revoke failed', error))
    }

    await apiRequest('/method/logout', { method: 'POST' })
  } finally {
    clearLocalCredentials()
  }
}

/** Full reload onto the login page so no signed-in state survives in memory. */
export function reloadToLogin() {
  window.location.hash = '#/login'
  window.location.reload()
}
