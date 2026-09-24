import { http } from '@shared/utils/httpClient.js'

const MEDIA_BASE = '/api/media/clips'

// media_service — «Живое фото» (модуль 7 ТЗ). Перенесено сюда из
// living-memory/api.js при разделении «Живой памяти» (форум краеведов) и
// «Живого фото» (AI-оживление) на отдельные вкладки.
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

// media_service принимает только изображения (JPEG/PNG/WebP, ≤15МБ).
export function uploadSourcePhoto(token, file) {
  return http.upload('/api/media/uploads', file, { token })
}
