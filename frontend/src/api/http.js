import { API_BASE_URL } from './config'

function buildUrl(path) {
  if (path.startsWith('http')) {
    return path
  }

  return `${API_BASE_URL}${path}`
}

function getAuthToken() {
  return localStorage.getItem('authToken')
}

function getStoredCsrfToken() {
  const csrfToken = window.frappe?.csrf_token

  return csrfToken && csrfToken !== 'None' ? csrfToken : ''
}

async function fetchCsrfToken() {
  const response = await fetch(
    buildUrl('/method/buy_in_minutes.auth.get_csrf_token'),
    {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    },
  )
  const data = await parseResponse(response)

  if (!response.ok) {
    const message = getFrappeErrorMessage(data) || 'Unable to prepare request'
    throw new Error(message)
  }

  const csrfToken = data?.message?.csrf_token
  window.frappe = window.frappe || {}
  window.frappe.csrf_token = csrfToken

  return csrfToken
}

async function parseResponse(response) {
  const contentType = response.headers.get('content-type') || ''

  if (contentType.includes('application/json')) {
    return response.json()
  }

  return response.text()
}

function getFrappeErrorMessage(data) {
  if (typeof data === 'string') {
    return data
  }

  if (data?._server_messages) {
    try {
      const messages = Array.isArray(data._server_messages)
        ? data._server_messages
        : JSON.parse(data._server_messages)
      const firstMessage = typeof messages[0] === 'string'
        ? JSON.parse(messages[0])
        : messages[0]

      return firstMessage?.message || firstMessage?._error_message || ''
    } catch (error) {
      return data._server_messages
    }
  }

  if (typeof data?.message === 'string') {
    return data.message
  }

  if (typeof data?.message?.message === 'string') {
    return data.message.message
  }

  if (typeof data?.error === 'string') {
    return data.error
  }

  if (typeof data?.exception === 'string') {
    return data.exception
  }

  if (typeof data?._message === 'string') {
    return data._message
  }

  if (typeof data?._error_message === 'string') {
    return data._error_message
  }

  if (typeof data?.exc === 'string') {
    return data.exc
  }

  if (Array.isArray(data?.exc) && data.exc.length) {
    return data.exc.join('\n')
  }

  return ''
}

export async function apiRequest(path, options = {}) {
  const token = getAuthToken()
  const method = (options.method || 'GET').toUpperCase()
  const needsCsrfToken = !['GET', 'HEAD', 'OPTIONS'].includes(method)
  const csrfToken = needsCsrfToken
    ? getStoredCsrfToken() || (await fetchCsrfToken())
    : ''
  const headers = {
    Accept: 'application/json',
    ...options.headers,
  }

  if (options.body && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  if (csrfToken && needsCsrfToken) {
    headers['X-Frappe-CSRF-Token'] = csrfToken
  }

  const response = await fetch(buildUrl(path), {
    ...options,
    credentials: options.credentials || 'include',
    headers,
  })

  const data = await parseResponse(response)

  if (!response.ok) {
    const message =
      getFrappeErrorMessage(data) ||
      response.statusText ||
      `API request failed (${response.status})`
    throw new Error(message)
  }

  return data
}
