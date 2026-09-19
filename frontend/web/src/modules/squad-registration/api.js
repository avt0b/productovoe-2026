import { http } from '@shared/utils/httpClient.js'

const BASE = '/api/search-hq/squads'

// Отряды — реальный бэкенд (search_hq_service, POST /squads уже существует).
export function createSquad(token, payload) {
  return http.post(BASE, payload, { token })
}

export function listMySquads(token, leaderId) {
  // У search_hq_service нет ?leader_id, поэтому берём максимальную страницу
  // (limit=200 — потолок, заданный бэкендом) и фильтруем на фронте по
  // Squad.leader_id, которое возвращается в SquadOut.
  return http.get(`${BASE}?limit=200`, { token }).then((squads) => squads.filter((s) => s.leader_id === leaderId))
}

// Список отрядов для выбора «предпочитаемого гида» в заявке школы на
// экскурсию — ручка публичная, токен не нужен (see squads.py list_squads).
export function listSquadsForGuideChoice() {
  return http.get(`${BASE}?limit=200`)
}
