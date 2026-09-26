import { apiRequest } from '@/core/api'

import * as mock from './mock'

/**
 * Механика «Я потерялся»: тревога на прогулке, кто её видит и где все на карте.
 * Ручки и объект — по CONTRACT 1.3–1.5. Пока бэкенда нет, `VITE_MOCK_NEW_API`
 * переключает каждую функцию на заглушку из `mock.ts`: переход на живой
 * бэкенд — это выключить флаг.
 */
const MOCK = import.meta.env.VITE_MOCK_NEW_API === 'true'

export type LostAlertStatus = 'active' | 'found' | 'cancelled' | 'expired'
export type LostAlertKind = 'self' | 'reported'
export type LostAlertRole = 'lost' | 'watcher' | 'observer'

export interface LostPosition {
  lat: number
  lon: number
  accuracy_m: number | null
  updated_at: string
}

export interface LostPerson {
  user_id: string
  display_name: string
  avatar_url: string | null
  is_me: boolean
  position: LostPosition | null
}

export interface LostWatcher {
  user_id: string
  display_name: string
  avatar_url: string | null
  relation: 'family' | 'guide'
  is_me: boolean
  responding: boolean
  responded_at: string | null
  position: LostPosition | null
  distance_m: number | null
}

export interface LostAlert {
  id: string
  excursion_id: string
  excursion_title: string
  status: LostAlertStatus
  kind: LostAlertKind
  my_role: LostAlertRole
  message: string
  lost: LostPerson
  raised_by: { user_id: string; display_name: string }
  watchers: LostWatcher[]
  created_at: string
  resolved_at: string | null
  resolved_by: { user_id: string; display_name: string } | null
}

export interface RaiseLostBody {
  lost_user_id?: string | null
  lat?: number
  lon?: number
  accuracy_m?: number | null
  message?: string
}

/** Все id — через encodeURIComponent, как в modules/excursions/data.ts. */
const enc = encodeURIComponent

export function raiseLost(excursionId: string, body: RaiseLostBody): Promise<LostAlert> {
  if (MOCK) return mock.raiseLost(excursionId, body)
  return apiRequest('POST', 'hq', `/excursions/${enc(excursionId)}/lost`, { auth: true, body })
}

export function fetchActiveAlerts(): Promise<LostAlert[]> {
  if (MOCK) return mock.fetchActiveAlerts()
  return apiRequest('GET', 'hq', '/lost-alerts/active', { auth: true })
}

export function fetchAlert(alertId: string): Promise<LostAlert> {
  if (MOCK) return mock.fetchAlert(alertId)
  return apiRequest('GET', 'hq', `/lost-alerts/${enc(alertId)}`, { auth: true })
}

export function respondAlert(alertId: string): Promise<LostAlert> {
  if (MOCK) return mock.respondAlert(alertId)
  return apiRequest('POST', 'hq', `/lost-alerts/${enc(alertId)}/respond`, { auth: true })
}

export function resolveAlert(alertId: string): Promise<LostAlert> {
  if (MOCK) return mock.resolveAlert(alertId)
  return apiRequest('POST', 'hq', `/lost-alerts/${enc(alertId)}/resolve`, { auth: true })
}

export function cancelAlert(alertId: string): Promise<LostAlert> {
  if (MOCK) return mock.cancelAlert(alertId)
  return apiRequest('POST', 'hq', `/lost-alerts/${enc(alertId)}/cancel`, { auth: true })
}

/**
 * Своя копия отправки точки, а не импорт из modules/excursions: фича модули не
 * импортирует. Ручка та же, что у прогулки (CONTRACT 1.2, правило 7).
 */
export function reportMyPosition(
  excursionId: string,
  position: { lat: number; lon: number; accuracy_m: number | null },
): Promise<void> {
  if (MOCK) return mock.reportMyPosition(excursionId, position)
  return apiRequest('PUT', 'hq', `/excursions/${enc(excursionId)}/walk/position`, { auth: true, body: position })
}
