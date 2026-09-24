import { http } from '@shared/utils/httpClient.js'

const ARCHIVE_BASE = '/api/archive/entries'

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

// Та же ручка, что и для фото документа/героя семьи — media_service
// принимает только изображения (JPEG/PNG/WebP, ≤15МБ). Аудиовоспоминания
// пока приложить нельзя — см. LIVING_MEMORY_BACKEND.md, media_service не
// принимает аудио.
export function uploadEntryPhoto(token, file) {
  return http.upload('/api/media/uploads', file, { token })
}
