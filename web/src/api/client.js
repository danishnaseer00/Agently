import { API_BASE } from '../utils/constants.js'

async function request(url, options = {}) {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`)
  }
  return res.json()
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
 * Upload a file (multipart/form-data) to the API.
 */
export async function uploadFile(url, file, params = {}) {
  const formData = new FormData()
  formData.append('file', file)

  const query = new URLSearchParams(params).toString()
  const fullUrl = query ? `${url}?${query}` : url

  const res = await fetch(`${API_BASE}${fullUrl}`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) return null
  return res.json()
}
