import { http } from '@shared/utils/httpClient.js'

const BASE = '/api/users/profiles'
const FAMILY_HEROES_BASE = '/api/users/family-heroes'

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

// Семейное древо (user_service, family_heroes) — приватная история семьи,
// правит только владелец. Список героев уже приходит вместе с профилем
// (ProfileOut.heroes), отдельная GET /family-heroes/mine фронту не нужна.
export function createFamilyHero(token, payload) {
  return http.post(FAMILY_HEROES_BASE, payload, { token })
}

export function updateFamilyHero(token, heroId, payload) {
  return http.patch(`${FAMILY_HEROES_BASE}/${heroId}`, payload, { token })
}

export function deleteFamilyHero(token, heroId) {
  return http.delete(`${FAMILY_HEROES_BASE}/${heroId}`, { token })
}

// Тот же media_service /uploads, что и для документа верификации — фото
// героя семьи (диплом, портрет), отдельной ручки под это тоже нет.
export function uploadFamilyHeroPhoto(token, file) {
  return http.upload('/api/media/uploads', file, { token })
}
