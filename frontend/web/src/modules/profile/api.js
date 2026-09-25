import { http } from '@shared/utils/httpClient.js'

const BASE = '/api/users/profiles'
const FAMILY_HEROES_BASE = '/api/users/family-heroes'

export function getMyProfile(token) {
  return http.get(`${BASE}/me`, { token })
}

export function updateMyProfile(token, payload) {
  return http.put(`${BASE}/me`, payload, { token })
}

// Значки за активность — начисляются на бэкенде за разные действия
// (завершение маршрута, верификация записи, выезд/донат), фронт только
// запрашивает готовый список.
export function getMyAchievements(token) {
  return http.get('/api/users/achievements/me', { token })
}

// Загрузка принимает только изображения (JPEG/PNG/WebP, ≤15МБ) — этого
// достаточно для фото документа (диплом, членский билет краеведческого
// общества и т.п.), отдельной ручки под документы нет.
export function uploadVerificationDocument(token, file) {
  return http.upload('/api/media/uploads', file, { token })
}

// Семейное древо — приватная история семьи, правит только владелец. Список
// героев уже приходит вместе с профилем, отдельный запрос фронту не нужен.
export function createFamilyHero(token, payload) {
  return http.post(FAMILY_HEROES_BASE, payload, { token })
}

export function updateFamilyHero(token, heroId, payload) {
  return http.patch(`${FAMILY_HEROES_BASE}/${heroId}`, payload, { token })
}

export function deleteFamilyHero(token, heroId) {
  return http.delete(`${FAMILY_HEROES_BASE}/${heroId}`, { token })
}

// Та же ручка загрузки, что и для документа верификации — фото героя семьи
// (диплом, портрет), отдельной ручки под это тоже нет.
export function uploadFamilyHeroPhoto(token, file) {
  return http.upload('/api/media/uploads', file, { token })
}
