import { http } from '@shared/utils/httpClient.js'

const BASE = '/api/search'

// Коллективные и индивидуальные заявки на экскурсии (модуль 5 ТЗ) — реальный
// бэкенд: экскурсия создаётся гидом заранее, участник записывается на неё —
// как один человек (organization_name пусто, group_size=1) или как группа
// (школа/клуб указывает organization_name и group_size), см.
// search_hq_service/api/routers/excursions.py.
export function listUpcomingExcursions() {
  return http.get(`${BASE}/excursions?upcoming_only=true&limit=100`)
}

export function registerForExcursion(token, excursionId, { organizationName = '', groupSize = 1 } = {}) {
  return http.post(
    `${BASE}/excursions/${excursionId}/registrations`,
    { organization_name: organizationName, group_size: groupSize },
    { token },
  )
}

export function getGuideRating(guideId) {
  return http.get(`${BASE}/guides/${guideId}/rating`)
}

// { guiding: Excursion[], joined: Excursion[] } — экскурсии, которые я веду
// как гид, и те, на которые я записан (сам или через свою школу/клуб).
export function getMyExcursions(token) {
  return http.get(`${BASE}/excursions/mine`, { token })
}
