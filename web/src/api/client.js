import { API_BASE } from '../utils/constants.js'

let _authToken = null
let _refreshToken = null

/**
 * Set the current auth token to include in all API requests.
 */
export function setAuthToken(token) {
  _authToken = token
}

/**
 * Set a callback to refresh the token when a 401 is received.
 * The callback should return the new token (or null if refresh fails).
 */
export function setTokenRefresh(fn) {
  _refreshToken = fn
}

/**
 * Get the auth headers object for direct fetch calls (e.g. chat SSE).
 */
export function getAuthHeaders() {
  return _authToken ? { Authorization: `Bearer ${_authToken}` } : {}
}

/**
 * Try to refresh the auth token via the registered callback.
 * Returns true if the token was refreshed, false otherwise.
 */
export async function refreshAuthToken() {
  if (!_refreshToken) return false
  try {
    const newToken = await _refreshToken()
    if (newToken) {
      _authToken = newToken
      return true
    }
  } catch {
    // Refresh failed
  }
  return false
}

function authHeaders() {
  return getAuthHeaders()
}

async function request(url, options = {}) {
  let retries = 0

  const doFetch = async () => {
    const res = await fetch(`${API_BASE}${url}`, {
      headers: { 'Content-Type': 'application/json', ...authHeaders(), ...options.headers },
      ...options,
    })

    // On 401, try refreshing the token once and retry
    if (res.status === 401 && retries < 1) {
      retries++
      const refreshed = await refreshAuthToken()
      if (refreshed) {
        return doFetch()
      }
    }

    if (!res.ok) {
      throw new Error(`API error: ${res.status} ${res.statusText}`)
    }
    return res.json()
  }

  return doFetch()
}

export async function get(url) {
  return request(url, { method: 'GET' })
}

export async function post(url, body) {
  return request(url, { method: 'POST', body: JSON.stringify(body) })
}

export async function patch(url, body) {
  return request(url, { method: 'PATCH', body: JSON.stringify(body) })
}

export async function del(url) {
  return request(url, { method: 'DELETE' })
}

/**
 * Upload a file (multipart/form-data) to the API with auth.
 */
export async function uploadFile(url, file, params = {}) {
  const formData = new FormData()
  formData.append('file', file)

  const query = new URLSearchParams(params).toString()
  const fullUrl = query ? `${url}?${query}` : url

  const res = await fetch(`${API_BASE}${fullUrl}`, {
    method: 'POST',
    headers: authHeaders(),
    body: formData,
  })
  if (!res.ok) return null
  return res.json()
}
