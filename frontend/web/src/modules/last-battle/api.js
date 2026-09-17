import { http } from '@shared/utils/httpClient.js'

const BASE = '/api/map/last-stand'

export function listLastStand({ status } = {}) {
  const params = new URLSearchParams()
  if (status) params.set('status', status)
  const qs = params.toString()
  return http.get(`${BASE}${qs ? `?${qs}` : ''}`)
}

export function createLastStand(token, payload) {
  return http.post(BASE, payload, { token })
}

export function setLastStandStatus(token, id, statusValue) {
  return http.patch(`${BASE}/${id}/status`, { status: statusValue }, { token })
}
