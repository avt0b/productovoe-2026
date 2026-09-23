import { http } from '@shared/utils/httpClient.js'

const BASE = '/api/search'

export function listNeeds({ kind, status = 'open' } = {}) {
  const params = new URLSearchParams({ status })
  if (kind) params.set('kind', kind)
  return http.get(`${BASE}/needs?${params.toString()}`)
}

export function listSquads() {
  return http.get(`${BASE}/squads`)
}

export function donate(token, needId, { amount, comment }) {
  return http.post(`${BASE}/needs/${needId}/donations`, { amount, comment }, { token })
}
