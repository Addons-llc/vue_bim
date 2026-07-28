import { apiRequest } from './http'

function encodeQueryValue(value) {
  if (Array.isArray(value) || typeof value === 'object') {
    return JSON.stringify(value)
  }

  return value
}

function buildResourcePath(doctype, params = {}) {
  const query = new URLSearchParams()

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, encodeQueryValue(value))
    }
  })

  const resourcePath = `/resource/${encodeURIComponent(doctype)}`
  const queryString = query.toString()

  return queryString ? `${resourcePath}?${queryString}` : resourcePath
}

export async function getDocTypeList(doctype, params = {}) {
  const response = await apiRequest(buildResourcePath(doctype, params))

  return response.data || []
}

export async function getDocTypeByName(doctype, name, params = {}) {
  const response = await apiRequest(
    `${buildResourcePath(doctype)}/${encodeURIComponent(name)}${
      Object.keys(params).length
        ? `?${new URLSearchParams(params).toString()}`
        : ''
    }`,
  )

  return response.data
}
