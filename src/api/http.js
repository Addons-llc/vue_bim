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

async function parseResponse(response) {
  const contentType = response.headers.get('content-type') || ''

  if (contentType.includes('application/json')) {
    return response.json()
  }

  return response.text()
}

function getFrappeErrorMessage(data) {
  if (data?._server_messages) {
    try {
      const messages = JSON.parse(data._server_messages)
      const firstMessage = JSON.parse(messages[0])

      return firstMessage.message
    } catch (error) {
      return data._server_messages
    }
  }

  return data?.message || data?.error || data?._error_message
}

export async function apiRequest(path, options = {}) {
  const token = getAuthToken()
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

  const response = await fetch(buildUrl(path), {
    ...options,
    credentials: options.credentials || 'include',
    headers,
  })

  const data = await parseResponse(response)

  if (!response.ok) {
    const message = getFrappeErrorMessage(data) || 'API request failed'
    throw new Error(message)
  }

  return data
}
