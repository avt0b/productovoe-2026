import { ApiError, apiRequest, withDemoFallback, type DataSource } from '@/core/api'
import { listLastStand } from '@/core/services/map'

import { DEMO_HQ } from './demo'

/**
 * Данные окна «Штаб» — `search_hq_service`: отряды, их потребности (сборы,
 * люди, снаряжение) и выезды «Выходные с поисковиком». Итоги сезона — из
 * «Последнего боя» (`map_service`).
 *
 * Типы повторяют схемы сервиса (`api/schemas/*.py`), поля в snake_case.
 * Сервис не ответил — демо-набор из `demo.ts` и плашка «демо-данные».
 */

export type NeedKind = 'funds' | 'volunteers' | 'equipment'
export type NeedStatus = 'open' | 'closed'

export interface Squad {
  id: string
  name: string
  region: string
  description: string
  contact: string
  leader_id: string
  created_at: string
}

export interface Need {
  id: string
  squad_id: string
  kind: NeedKind
  title: string
  description: string
  target_amount: number | null
  collected_amount: number
  status: NeedStatus
  created_at: string
}

export interface Trip {
  id: string
  squad_id: string
  title: string
  location: string
  /** День выезда, `YYYY-MM-DD`. */
  starts_on: string
  capacity: number
  description: string
  /** Чек-лист одной строкой: пункты через перевод строки или запятую. */
  checklist: string
  created_at: string
}

export interface Registration {
  id: string
  trip_id: string
  user_id: string
  status: 'registered' | 'cancelled'
  created_at: string
}

export interface Donation {
  id: string
  need_id: string
  amount: number
  comment: string
  created_at: string
}

export interface SeasonStats {
  discovered: number
  confirmed: number
  raised: number
  source: DataSource
}

export interface HqOverview {
  squads: Squad[]
  needs: Need[]
  trips: Trip[]
  /** Выезды, на которые человек записан. `null` — неизвестно: демо-режим или сервис без этой ручки. */
  myTripIds: Set<string> | null
  season: SeasonStats
  source: DataSource
}

export const NEED_KINDS: Record<NeedKind, { title: string; icon: string }> = {
  funds: { title: 'Сбор средств', icon: 'payments' },
  volunteers: { title: 'Нужны люди', icon: 'group_add' },
  equipment: { title: 'Нужно снаряжение', icon: 'construction' },
}

export async function fetchHq(withAccount: boolean): Promise<HqOverview> {
  const [live, season] = await Promise.all([
    withDemoFallback(
      async () => {
        const [squads, needs, trips] = await Promise.all([
          apiRequest<Squad[]>('GET', 'hq', '/squads'),
          apiRequest<Need[]>('GET', 'hq', '/needs', { query: { status: 'open' } }),
          apiRequest<Trip[]>('GET', 'hq', '/trips', { query: { upcoming_only: true } }),
        ])
        return { squads, needs, trips }
      },
      () => DEMO_HQ,
    ),
    fetchSeason(),
  ])

  const myTripIds = live.source === 'live' && withAccount ? await fetchMyTripIds() : null
  return { ...live.data, myTripIds, season, source: live.source }
}

/** Мои выезды. Старый сервис без `/trips/mine` — не знаем, экран просто не отметит записанные. */
async function fetchMyTripIds(): Promise<Set<string> | null> {
  try {
    const trips = await apiRequest<Trip[]>('GET', 'hq', '/trips/mine', { auth: true })
    return new Set(trips.map((trip) => trip.id))
  } catch (reason) {
    if (reason instanceof ApiError && (reason.status === 404 || reason.status === 422)) return null
    throw reason
  }
}

/** Итоги по местам «Последнего боя»: сколько найдено, подтверждено архивом, поднято. */
async function fetchSeason(): Promise<SeasonStats> {
  const { data, source } = await listLastStand()
  const count = (status: string): number => data.filter((point) => point.status === status).length
  return {
    discovered: count('discovered'),
    confirmed: count('archive_confirmed'),
    raised: count('remains_raised'),
    source,
  }
}

const needPath = (needId: string, rest = ''): string => `/needs/${encodeURIComponent(needId)}${rest}`
const tripPath = (tripId: string, rest = ''): string => `/trips/${encodeURIComponent(tripId)}${rest}`
const squadPath = (squadId: string, rest = ''): string => `/squads/${encodeURIComponent(squadId)}${rest}`

export function fetchNeed(needId: string): Promise<Need> {
  return apiRequest('GET', 'hq', needPath(needId))
}

export function fetchDonations(needId: string): Promise<Donation[]> {
  return apiRequest('GET', 'hq', needPath(needId, '/donations'))
}

export function donate(needId: string, amount: number, comment: string): Promise<Donation> {
  return apiRequest('POST', 'hq', needPath(needId, '/donations'), { body: { amount, comment }, auth: true })
}

export function registerForTrip(tripId: string): Promise<Registration> {
  return apiRequest('POST', 'hq', tripPath(tripId, '/registrations'), { auth: true })
}

export function cancelTripRegistration(tripId: string): Promise<void> {
  return apiRequest('DELETE', 'hq', tripPath(tripId, '/registrations/me'), { auth: true })
}

/** Кто записался — только командиру отряда и модератору. */
export function fetchTripRegistrations(tripId: string): Promise<Registration[]> {
  return apiRequest('GET', 'hq', tripPath(tripId, '/registrations'), { auth: true })
}

export interface SquadDraft {
  name: string
  region: string
  description: string
  contact: string
}

export function createSquad(draft: SquadDraft): Promise<Squad> {
  return apiRequest('POST', 'hq', '/squads', { body: draft, auth: true })
}

export interface TripDraft {
  title: string
  location: string
  starts_on: string
  capacity: number
  description: string
  checklist: string
}

export function createTrip(squadId: string, draft: TripDraft): Promise<Trip> {
  return apiRequest('POST', 'hq', squadPath(squadId, '/trips'), { body: draft, auth: true })
}

export interface NeedDraft {
  kind: NeedKind
  title: string
  description: string
  target_amount: number | null
}

export function createNeed(squadId: string, draft: NeedDraft): Promise<Need> {
  return apiRequest('POST', 'hq', squadPath(squadId, '/needs'), { body: draft, auth: true })
}

export function closeNeed(needId: string): Promise<Need> {
  return apiRequest('POST', 'hq', needPath(needId, '/close'), { auth: true })
}

/** Пункты чек-листа: сервис хранит их одной строкой. */
export function checklistItems(checklist: string): string[] {
  return checklist
    .split(/\n|,|;/)
    .map((item) => item.trim())
    .filter(Boolean)
}
