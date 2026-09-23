import { http } from '@shared/utils/httpClient.js'

const BASE = '/api/routes/routes'
const POI_BASE = '/api/map/poi'

// Слой «ВОВ» (map_service): захоронения, памятники, места боёв и т.д.
// Ручка публичная, токен не нужен (map_service/api/routers/poi.py list_poi).
export function listPoi(kind) {
  const params = kind ? `?kind=${kind}&limit=200` : '?limit=200'
  return http.get(`${POI_BASE}${params}`)
}

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
