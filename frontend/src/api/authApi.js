import { apiRequest, clearStoredCsrfToken } from './http'
import { CHECKOUT_RESUME_TOKEN_STORAGE_KEY } from './paymentApi'
import { clearCurrentUser } from '../data/authStore'
import { appUrl } from '../router/base'

export const AUTH_TOKEN_STORAGE_KEY = 'authToken'
export const AUTH_FLOW_TOKEN_STORAGE_KEY = 'authFlowToken'
// A new Google sign-up has no account until its phone is OTP-verified; this
// short-lived token stands in for it until then.
const GOOGLE_SIGNUP_TOKEN_STORAGE_KEY = 'googleSignupToken'

export function getGoogleSignupToken() {
  return sessionStorage.getItem(GOOGLE_SIGNUP_TOKEN_STORAGE_KEY) || ''
}

export function clearGoogleSignupToken() {
  sessionStorage.removeItem(GOOGLE_SIGNUP_TOKEN_STORAGE_KEY)
}

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

// Attaches a phone number to the signed-in account, or, during a new Google
// sign-up, to the account that verifying the OTP will create.
export function requestLinkPhoneOtp(phoneNumber) {
  const signupToken = getGoogleSignupToken()

  return apiRequest('/method/buy_in_minutes.auth.request_link_phone_otp', {
    method: 'POST',
    body: JSON.stringify({
      phone_number: phoneNumber,
      ...(signupToken ? { signup_token: signupToken } : {}),
    }),
  })
}

export async function verifyLinkPhoneOtp(phoneNumber, otp, authFlowToken) {
  const response = await apiRequest('/method/buy_in_minutes.auth.verify_link_phone_otp', {
    method: 'POST',
    body: JSON.stringify({
      phone_number: phoneNumber,
      otp,
      auth_flow_token: authFlowToken,
      ...(getGoogleSignupToken() ? { signup_token: getGoogleSignupToken() } : {}),
    }),
  })

  if (response?.message?.success) {
    storeAuthToken(response)
    clearStoredCsrfToken()
    clearGoogleSignupToken()
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
    body: JSON.stringify({ access_token: accessToken, defer_signup: 1 }),
  })

  const result = response?.message
  if (result?.success && result.signup_token) {
    // New email: not signed in yet, the phone step creates the account.
    sessionStorage.setItem(GOOGLE_SIGNUP_TOKEN_STORAGE_KEY, result.signup_token)
  } else if (result?.success) {
    clearGoogleSignupToken()
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
  clearGoogleSignupToken()
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
  window.location.assign(appUrl('/login'))
}
