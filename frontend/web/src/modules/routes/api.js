import { http } from '@shared/utils/httpClient.js'

const BASE = '/api/routes/routes'
const POI_BASE = '/api/map/poi'
const ARCHIVE_ENTRIES_BASE = '/api/archive/entries'

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

// Отметка прогресса по точкам (progress/start, progress/me, progress/
// complete-waypoint) — сценарий «иду по тропе прямо сейчас» живёт только в
// мобильном приложении (frontend/client, там же GPS/AR/NFC для точки на
// месте). На web остаётся только просмотр маршрута для планирования.

// archive_service: «народный архив» — неподтверждённые записи в прямоугольнике
// вокруг маршрута, витрина для подсказки «рядом есть неподтверждённая заметка,
// помоги проверить» (entries.py: GET /entries/nearby-pending). Публичная ручка,
// токен не нужен.
export function listNearbyPendingEntries({ minLat, minLon, maxLat, maxLon }) {
  const params = new URLSearchParams({
    min_lat: minLat,
    min_lon: minLon,
    max_lat: maxLat,
    max_lon: maxLon,
    limit: 50,
  })
  return http.get(`${ARCHIVE_ENTRIES_BASE}/nearby-pending?${params}`)
}

// Проверить может поисковик/краевед/наставник/модератор (EntryService.VERIFIER_ROLES).
export function verifyArchiveEntry(token, entryId, note = '') {
  return http.post(`${ARCHIVE_ENTRIES_BASE}/${entryId}/verify`, { note }, { token })
}

export function rejectArchiveEntry(token, entryId, note = '') {
  return http.post(`${ARCHIVE_ENTRIES_BASE}/${entryId}/reject`, { note }, { token })
}
