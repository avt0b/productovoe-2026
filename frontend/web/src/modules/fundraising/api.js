import { http } from '@shared/utils/httpClient.js'

const BASE = '/api/search-hq'

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

// Коллективные заявки школ/клубов на экскурсии (модуль 5 ТЗ) — реальный
// бэкенд: экскурсия создаётся гидом заранее, школа записывается на неё как
// группа через organization_name/group_size (search_hq_service/api/routers/excursions.py).
export function listUpcomingExcursions() {
  return http.get(`${BASE}/excursions?upcoming_only=true&limit=100`)
}

export function registerForExcursion(token, excursionId, { organizationName, groupSize }) {
  return http.post(
    `${BASE}/excursions/${excursionId}/registrations`,
    { organization_name: organizationName, group_size: groupSize },
    { token },
  )
}

export function getGuideRating(guideId) {
  return http.get(`${BASE}/guides/${guideId}/rating`)
}
