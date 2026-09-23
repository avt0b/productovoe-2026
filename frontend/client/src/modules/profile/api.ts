import { apiGet, apiRequest } from '@/core/api'

/**
 * Профиль исследователя из `user_service` (8002).
 *
 * Поля повторяют схему `ProfileOut` один в один — ничего сверх того, что
 * отдаёт бэкенд, здесь не появляется.
 */
export interface Profile {
  id: string
  display_name: string
  city: string
  bio: string
  avatar_url: string | null
  role: string
  squad_id: string | null
  is_verified: boolean
  subscribed_to_search: boolean
  alert_radius_km: number
  home_lat: number | null
  home_lon: number | null
  achievements: Achievement[]
  created_at: string
}

/** Достижение приходит голым кодом и датой — названия и значки живут на клиенте. */
export interface Achievement {
  code: string
  earned_at: string
}

/** Что разрешено менять: схема `ProfileUpdate`, все поля необязательные. */
export interface ProfilePatch {
  display_name?: string
  city?: string
  bio?: string
  avatar_url?: string | null
  squad_id?: string | null
  subscribed_to_search?: boolean
  alert_radius_km?: number
  home_lat?: number | null
  home_lon?: number | null
}

export function fetchMyProfile(): Promise<Profile> {
  return apiRequest<Profile>('GET', 'users', '/profiles/me', { auth: true })
}

export function updateMyProfile(patch: ProfilePatch): Promise<Profile> {
  return apiRequest<Profile>('PUT', 'users', '/profiles/me', { auth: true, body: patch })
}

/**
 * Свои достижения. Отдельной ручкой, хотя они есть и в профиле: там список
 * приходит вместе с остальным и не обновляется без перезапроса всего профиля.
 */
export function fetchMyAchievements(): Promise<Achievement[]> {
  return apiRequest<Achievement[]>('GET', 'users', '/achievements/me', { auth: true })
}

/**
 * Загрузка картинки профиля. `user_service` принимает JPEG, PNG и WebP до 5 МБ
 * и возвращает ссылку — её потом сохраняют в профиль как `avatar_url`.
 * Пока хранилище не поднято, ручка отвечает 503.
 */
export async function uploadAvatar(file: File): Promise<string> {
  const form = new FormData()
  form.append('file', file)
  const { url } = await apiRequest<{ url: string }>('POST', 'users', '/uploads', { auth: true, body: form })
  return url
}

/** Проверка токена без загрузки профиля — пригодится там, где нужен только факт входа. */
export function whoami(): Promise<{ user_id: string; role: string }> {
  return apiGet('users', '/whoami')
}
