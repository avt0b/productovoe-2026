import { http } from '@shared/utils/httpClient.js'

const BASE = '/api/auth'

export function register({ email, password, role }) {
  return http.post(`${BASE}/register`, { email, password, role })
}

export function login({ email, password }) {
  return http.post(`${BASE}/login`, { email, password })
}

export function refresh(refreshToken) {
  return http.post(`${BASE}/refresh`, { refresh_token: refreshToken })
}

export function logout(refreshToken) {
  return http.post(`${BASE}/logout`, { refresh_token: refreshToken })
}

export function me(accessToken) {
  return http.get(`${BASE}/me`, { token: accessToken })
}
