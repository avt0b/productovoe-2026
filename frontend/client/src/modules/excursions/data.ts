import { apiRequest } from '@/core/api'
import type { UserPosition } from '@/core/geo'
import type { UserRole } from '@/core/session'

/**
 * Данные окна «Экскурсии» — `search_hq_service` (`/excursions`).
 *
 * Типы повторяют схемы сервиса (`api/schemas/excursion.py`), поля в snake_case,
 * как в ответе. Сама встряска — модуль `features/bump`. Демо-набора нет намеренно: запись и бамп без сервера ничего не
 * значат, экран честно показывает ошибку.
 */

export type ExcursionStatus = 'scheduled' | 'gathering' | 'finished' | 'cancelled'

export interface ExcursionViewer {
  is_guide: boolean
  registered: boolean
  checked_in_at: string | null
}

export interface Excursion {
  id: string
  guide_id: string
  title: string
  description: string
  place_name: string
  lat: number
  lon: number
  poi_id: string | null
  starts_at: string
  capacity: number
  status: ExcursionStatus
  gathering_started_at: string | null
  gathering_ends_at: string | null
  registered_count: number
  checked_in_count: number
  /** Кем экскурсия приходится смотрящему. `null` — запрос без аккаунта. */
  viewer: ExcursionViewer | null
  created_at: string
}

export interface MyExcursions {
  guiding: Excursion[]
  joined: Excursion[]
}

export interface Gathering {
  excursion_id: string
  status: ExcursionStatus
  is_open: boolean
  started_at: string | null
  ends_at: string | null
  registered_count: number
  checked_in_count: number
  /** Кто пришёл — только у краеведа. */
  checked_in: { user_id: string; checked_in_at: string }[]
  my_checked_in_at: string | null
}

export interface Position {
  lat: number
  lon: number
  accuracy_m: number | null
}

export interface ExcursionDraft {
  title: string
  description: string
  place_name: string
  lat: number
  lon: number
  poi_id: string | null
  starts_at: string
  capacity: number
}

/** Кто водит экскурсии — как `GUIDE_ROLES` в search_hq_service. */
const GUIDE_ROLES: ReadonlySet<UserRole> = new Set<UserRole>(['local_historian', 'mentor', 'moderator'])

export function isGuideRole(role: UserRole | undefined): boolean {
  return role !== undefined && GUIDE_ROLES.has(role)
}

export function toPosition(position: UserPosition): Position {
  return { lat: position.lat, lon: position.lon, accuracy_m: Math.round(position.accuracyMeters) }
}

const path = (excursionId: string, rest = ''): string => `/excursions/${encodeURIComponent(excursionId)}${rest}`

/** Список публичный: без аккаунта тоже видно, куда можно прийти. С токеном сервис добавляет `viewer`. */
export function fetchExcursions(withAccount: boolean): Promise<Excursion[]> {
  return apiRequest('GET', 'hq', '/excursions', { query: { upcoming_only: true }, auth: withAccount })
}

export function fetchMyExcursions(): Promise<MyExcursions> {
  return apiRequest('GET', 'hq', '/excursions/mine', { auth: true })
}

export function fetchExcursion(excursionId: string, withAccount: boolean): Promise<Excursion> {
  return apiRequest('GET', 'hq', path(excursionId), { auth: withAccount })
}

export function createExcursion(draft: ExcursionDraft): Promise<Excursion> {
  return apiRequest('POST', 'hq', '/excursions', { body: draft, auth: true })
}

export function cancelExcursion(excursionId: string): Promise<Excursion> {
  return apiRequest('POST', 'hq', path(excursionId, '/cancel'), { auth: true })
}

export function registerForExcursion(excursionId: string): Promise<unknown> {
  return apiRequest('POST', 'hq', path(excursionId, '/registrations'), { auth: true })
}

export function cancelRegistration(excursionId: string): Promise<void> {
  return apiRequest('DELETE', 'hq', path(excursionId, '/registrations/me'), { auth: true })
}

export function startGathering(excursionId: string, position: Position): Promise<Gathering> {
  return apiRequest('POST', 'hq', path(excursionId, '/gathering/start'), { body: position, auth: true })
}

export function finishGathering(excursionId: string): Promise<Gathering> {
  return apiRequest('POST', 'hq', path(excursionId, '/gathering/finish'), { auth: true })
}

export function fetchGathering(excursionId: string): Promise<Gathering> {
  return apiRequest('GET', 'hq', path(excursionId, '/gathering'), { auth: true })
}
