import { apiRequest } from '@/core/api'

/**
 * Уведомления человека — `user_service` (`/notifications`).
 *
 * Их создают другие сервисы: search_hq_service, когда краевед открыл сбор,
 * map_service — когда рядом отметили «Последний бой». Приложение только читает
 * и отмечает прочитанными.
 */

export interface AppNotification {
  id: string
  kind: string
  title: string
  body: string
  payload: Record<string, unknown> | null
  read_at: string | null
  created_at: string
}

export function fetchNotifications(): Promise<AppNotification[]> {
  return apiRequest('GET', 'users', '/notifications', { auth: true })
}

export function markNotificationRead(id: string): Promise<AppNotification> {
  return apiRequest('POST', 'users', `/notifications/${encodeURIComponent(id)}/read`, { auth: true })
}
