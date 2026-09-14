import { http } from '@shared/utils/httpClient.js'

const BASE = '/api/archive/entries'

export function listVerifiedEntries({ kind } = {}) {
  const params = new URLSearchParams()
  if (kind) params.set('kind', kind)
  const qs = params.toString()
  return http.get(`${BASE}${qs ? `?${qs}` : ''}`)
}

export function listMyEntries(token) {
  return http.get(`${BASE}/mine`, { token })
}

export function createEntry(token, payload) {
  return http.post(BASE, payload, { token })
}
