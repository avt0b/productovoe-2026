import { http } from '@shared/utils/httpClient.js'

const BASE = '/api/users/profiles'

export function getMyProfile(token) {
  return http.get(`${BASE}/me`, { token })
}

export function updateMyProfile(token, payload) {
  return http.put(`${BASE}/me`, payload, { token })
}
