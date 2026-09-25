import { fetchNotifications, markNotificationRead, type AppNotification } from '@/features/notifications/api'

export type { AppNotification } from '@/features/notifications/api'

/**
 * Значок по виду уведомления — только оформление; куда вести по нажатию,
 * решает `useNotificationWatcher.ts` (там же и список известных видов).
 * Неизвестный вид всё равно попадает в список — просто с общей иконкой.
 */
const KIND_ICONS: Record<string, string> = {
  excursion_gathering_started: 'groups',
  excursion_walk_started: 'directions_walk',
  last_stand_nearby: 'person_search',
  trip_cancelled: 'event_busy',
  achievement: 'military_tech',
}

export function notificationIcon(kind: string): string {
  return KIND_ICONS[kind] ?? 'notifications'
}

export function listMyNotifications(): Promise<AppNotification[]> {
  return fetchNotifications()
}

export function markRead(id: string): Promise<AppNotification> {
  return markNotificationRead(id)
}

/**
 * «Прочитать всё» — своей ручки на бэке нет (см. `user_service/api/routers/notifications.py`),
 * поэтому отмечаем по одной, но все запросы разом.
 */
export async function markAllRead(unread: AppNotification[]): Promise<void> {
  await Promise.all(unread.map((item) => markNotificationRead(item.id)))
}
