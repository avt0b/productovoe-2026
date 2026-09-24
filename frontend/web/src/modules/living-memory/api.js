import { http } from '@shared/utils/httpClient.js'

const ARCHIVE_BASE = '/api/archive/entries'
const PROFILES_BASE = '/api/users/profiles'

// «Живая память» — народный архив (archive_service): малоизвестные подвиги,
// локальные события, карточки бойцов, не попавшие в федеральные базы.
// Публичная лента отдаёт только verified-записи (EntryService.search_public).
export function listVerifiedEntries({ kind } = {}) {
  const params = new URLSearchParams()
  if (kind) params.set('kind', kind)
  const qs = params.toString()
  return http.get(`${ARCHIVE_BASE}${qs ? `?${qs}` : ''}`)
}

export function listMyEntries(token) {
  return http.get(`${ARCHIVE_BASE}/mine`, { token })
}

export function createEntry(token, payload) {
  return http.post(ARCHIVE_BASE, payload, { token })
}

// Очередь модерации — доступна только поисковикам/краеведам/наставникам/
// модераторам (EntryService._can_verify), проверяется на самом бэке.
export function listModerationEntries(token, status = 'pending') {
  return http.get(`${ARCHIVE_BASE}/moderation?status=${status}`, { token })
}

export function verifyEntry(token, entryId, note = '') {
  return http.post(`${ARCHIVE_BASE}/${entryId}/verify`, { note }, { token })
}

export function rejectEntry(token, entryId, note = '') {
  return http.post(`${ARCHIVE_BASE}/${entryId}/reject`, { note }, { token })
}

export function uploadEntryPhoto(token, file) {
  return http.upload('/api/media/uploads', file, { token })
}

// Та же ручка /uploads — media_service сам определяет аудио по content-type
// файла (mp3/ogg/wav/m4a/webm, ≤30МБ) и кладёт результат в audio_url записи.
export function uploadEntryAudio(token, file) {
  return http.upload('/api/media/uploads', file, { token })
}

// Публичная ручка user_service без токена — имена авторов для ленты одним
// запросом, без N+1. Кого нет в ответе — тот не найден (удалённый аккаунт).
export function getAuthorsBatch(ids) {
  const unique = [...new Set(ids)].filter(Boolean)
  if (unique.length === 0) return Promise.resolve([])
  return http.get(`${PROFILES_BASE}/batch?ids=${unique.join(',')}`)
}
