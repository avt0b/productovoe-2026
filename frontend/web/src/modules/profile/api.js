import { http } from '@shared/utils/httpClient.js'

const BASE = '/api/users/profiles'

export function getMyProfile(token) {
  return http.get(`${BASE}/me`, { token })
}

export function updateMyProfile(token, payload) {
  return http.put(`${BASE}/me`, payload, { token })
}

// Значки за активность — начисляются другими сервисами (route_service на
// завершении маршрута, archive_service на верификации, search_hq_service на
// выезде/донате), user_service только хранит и отдаёт список.
export function getMyAchievements(token) {
  return http.get('/api/users/achievements/me', { token })
}

// media_service принимает только изображения (JPEG/PNG/WebP, ≤15МБ) — этого
// достаточно для фото документа (диплом, членский билет краеведческого
// общества и т.п.), отдельной ручки под документы на бэке нет.
export function uploadVerificationDocument(token, file) {
  return http.upload('/api/media/uploads', file, { token })
}
