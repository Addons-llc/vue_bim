import { GOOGLE_CLIENT_ID } from './config'

let googleIdentityPromise
let tokenClient
let pendingTokenRequest = null

export function loadGoogleIdentity() {
  if (window.google?.accounts?.oauth2) {
    return Promise.resolve(window.google.accounts)
  }

  if (!GOOGLE_CLIENT_ID) {
    return Promise.reject(new Error('Google client ID is missing.'))
  }

  if (!googleIdentityPromise) {
    googleIdentityPromise = new Promise((resolve, reject) => {
      const script = document.createElement('script')

      script.src = 'https://accounts.google.com/gsi/client?hl=en'
      script.async = true
      script.defer = true
      script.onload = () => resolve(window.google.accounts)
      script.onerror = () => {
        googleIdentityPromise = null
        reject(new Error('Unable to load Google sign-in.'))
      }

      document.head.appendChild(script)
    })
  }
  return googleIdentityPromise
}

function settleTokenRequest(error, accessToken) {
  const request = pendingTokenRequest
  pendingTokenRequest = null

  if (!request) {
    return
  }

  if (error) {
    request.reject(error)
  } else {
    request.resolve(accessToken)
  }
}

// Loads the script and creates the token client ahead of the click, so the
// popup opens straight from the user's tap and isn't blocked.
export async function prepareGoogleSignIn() {
  if (tokenClient) {
    return
  }

  const accounts = await loadGoogleIdentity()
  tokenClient = accounts.oauth2.initTokenClient({
    client_id: GOOGLE_CLIENT_ID,
    scope: 'openid email profile',
    callback: (response) => {
      if (response?.error || !response?.access_token) {
        settleTokenRequest(new Error(response?.error_description || 'Google sign-in failed. Please try again.'))
        return
      }

      settleTokenRequest(null, response.access_token)
    },
    error_callback: (error) => {
      const message = error?.type === 'popup_failed_to_open'
        ? 'Allow pop-ups for this site to sign in with Google.'
        : 'Google sign-in failed. Please try again.'
      // Closing the popup is the user changing their mind, not an error.
      settleTokenRequest(Object.assign(new Error(message), { cancelled: error?.type === 'popup_closed' }))
    },
  })
}

/** Opens Google's account picker; resolves with an access token. */
export async function requestGoogleAccessToken() {
  if (!tokenClient) {
    await prepareGoogleSignIn()
  }

  settleTokenRequest(Object.assign(new Error('Superseded'), { cancelled: true }))

  return new Promise((resolve, reject) => {
    pendingTokenRequest = { resolve, reject }
    tokenClient.requestAccessToken({ prompt: 'select_account' })
  })
}

/** Name and email of the Google account an access token belongs to. */
export async function fetchGoogleProfile(accessToken) {
  const response = await fetch('https://openidconnect.googleapis.com/v1/userinfo', {
    headers: { Authorization: `Bearer ${accessToken}` },
  })

  if (!response.ok) {
    throw new Error('Unable to read your Google profile. Please try again.')
  }

  const profile = await response.json()
  return { email: profile.email || '', fullName: profile.name || '' }
}
