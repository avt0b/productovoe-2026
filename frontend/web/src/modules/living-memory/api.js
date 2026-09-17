import { http } from '@shared/utils/httpClient.js'

const ARCHIVE_BASE = '/api/archive/entries'
const MEDIA_BASE = '/api/media/clips'

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

// media_service — «Живое фото»
export function listPublicClips() {
  return http.get(MEDIA_BASE)
}

export function listMyClips(token) {
  return http.get(`${MEDIA_BASE}/mine`, { token })
}

export function createClip(token, payload) {
  return http.post(MEDIA_BASE, payload, { token })
}

export function retryClip(token, clipId) {
  return http.post(`${MEDIA_BASE}/${clipId}/retry`, {}, { token })
}

export function shareClip(token, clipId, { recipient, note }) {
  return http.post(`${MEDIA_BASE}/${clipId}/shares`, { recipient, note }, { token })
}
