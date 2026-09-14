import { http } from '@shared/utils/httpClient.js'

const BASE = '/api/routes/routes'

export function listRoutes({ mode } = {}) {
  const params = new URLSearchParams()
  if (mode) params.set('mode', mode)
  const qs = params.toString()
  return http.get(`${BASE}${qs ? `?${qs}` : ''}`)
}

export function getRouteDetail(routeId) {
  return http.get(`${BASE}/${routeId}`)
}

export function startProgress(token, routeId) {
  return http.post(`${BASE}/${routeId}/progress/start`, {}, { token })
}

export function getMyProgress(token, routeId) {
  return http.get(`${BASE}/${routeId}/progress/me`, { token })
}

export function completeWaypoint(token, routeId, waypointId) {
  return http.post(`${BASE}/${routeId}/progress/complete-waypoint`, { waypoint_id: waypointId }, { token })
}
