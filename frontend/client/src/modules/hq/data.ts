import { ApiError, apiRequest, withDemoFallback, type DataSource } from '@/core/api'
import { plural } from '@/core/format'
import { OREL_CENTER, type LatLon } from '@/core/geo'
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

export type CampaignKind = 'raise' | 'equip' | 'other'

/**
 * Два целевых сбора из кейса. Отдельного поля в сервисе нет: вид стоит в
 * начале заголовка («Поднять бойца: ГСМ и генератор») — так пишут командиры
 * и сид, и так сбор одинаково читается в любом клиенте.
 */
export const CAMPAIGN_KINDS: Record<CampaignKind, { title: string; icon: string; hint: string }> = {
  raise: { title: 'Поднять бойца', icon: 'military_tech', hint: 'Бензин, генератор, дорога — без этого экспедиция не выйдет в поле' },
  equip: { title: 'Экипировать отряд', icon: 'construction', hint: 'Металлоискатели, щупы, палатки, форма для новичков' },
  other: { title: 'Другой сбор', icon: 'savings', hint: 'Любая другая цель отряда' },
}

export function campaignOf(need: Need): { kind: CampaignKind; headline: string } {
  const title = need.title.trim()
  for (const kind of ['raise', 'equip'] as const) {
    const prefix = CAMPAIGN_KINDS[kind].title
    if (title.toLowerCase().startsWith(prefix.toLowerCase())) {
      const headline = title.slice(prefix.length).replace(/^[\s:—–-]+/, '')
      return { kind, headline: headline ? headline[0].toUpperCase() + headline.slice(1) : title }
    }
  }
  return { kind: 'other', headline: title }
}

export function campaignTitle(kind: CampaignKind, headline: string): string {
  return kind === 'other' ? headline : `${CAMPAIGN_KINDS[kind].title}: ${headline}`
}

/**
 * Районные центры Орловщины. Координат у отряда в сервисе нет — только город
 * словами («Орёл», «Мценск»), по нему и ставим метку на карту потребностей.
 * Орёл последним: «Орловский район» и «Орловская область» не должны
 * перебить «Мценский район, Орловская область».
 */
const PLACES: { stem: string; point: LatLon }[] = [
  { stem: 'мценск', point: { lat: 53.2789, lon: 36.5746 } },
  { stem: 'болхов', point: { lat: 53.4436, lon: 36.0086 } },
  { stem: 'ливен', point: { lat: 52.4247, lon: 37.6044 } },
  { stem: 'ливн', point: { lat: 52.4247, lon: 37.6044 } },
  { stem: 'кром', point: { lat: 52.6881, lon: 35.7936 } },
  { stem: 'дмитровск', point: { lat: 52.5064, lon: 35.1442 } },
  { stem: 'новосил', point: { lat: 52.9747, lon: 37.045 } },
  { stem: 'малоархангельск', point: { lat: 52.4003, lon: 36.5039 } },
  { stem: 'орел', point: OREL_CENTER },
  { stem: 'орлов', point: OREL_CENTER },
]

export function squadPlace(squad: Squad): LatLon | null {
  const text = squad.region.toLowerCase().replaceAll('ё', 'е')
  return text ? (PLACES.find((place) => text.includes(place.stem))?.point ?? null) : null
}

export interface ContactLink {
  href: string
  label: string
  icon: string
}

/** Контакт штаба — свободная строка; ссылку делаем, только если узнали адрес, почту или телефон. */
export function contactLink(contact: string): ContactLink | null {
  const text = contact.trim()
  if (!text) return null
  const url = text.match(/https?:\/\/\S+/)?.[0] ?? (/^(t\.me|vk\.com|wa\.me)\//i.test(text) ? `https://${text}` : null)
  if (url) return { href: url, label: 'Написать отряду', icon: 'chat' }
  const email = text.match(/[^\s@]+@[^\s@]+\.[^\s@]+/)?.[0]
  if (email) return { href: `mailto:${email}`, label: 'Написать на почту', icon: 'mail' }
  const phone = text.replace(/[^\d+]/g, '')
  if (/^\+?\d{10,12}$/.test(phone)) return { href: `tel:${phone}`, label: 'Позвонить в штаб', icon: 'call' }
  return null
}

const WEEKDAY = new Intl.DateTimeFormat('ru-RU', { weekday: 'long' })
const WEEKDAY_SHORT = new Intl.DateTimeFormat('ru-RU', { weekday: 'short' })
const DAY_MONTH = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long' })
const MONTH_SHORT = new Intl.DateTimeFormat('ru-RU', { month: 'short' })

/** Фильтр календаря: `all` — все выезды, `mine` — куда записан, `YYYY-MM-DD` — один день. */
export type TripFilter = 'all' | 'mine' | (string & {})

export interface TripDay {
  /** «10 июня, суббота» — как в прототипе кейса. */
  long: string
  day: number
  month: string
  weekday: string
  /** «Сегодня», «Завтра», «Через 5 дней». */
  relative: string
}

/** День выезда — местная полночь, а не UTC: иначе к западу от Гринвича он уедет на день назад. */
export function tripDay(startsOn: string, now = new Date()): TripDay {
  const date = new Date(`${startsOn}T00:00:00`)
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const days = Math.round((date.getTime() - today.getTime()) / 86_400_000)
  const relative =
    days <= 0
      ? 'Сегодня'
      : days === 1
        ? 'Завтра'
        : days === 2
          ? 'Послезавтра'
          : `Через ${days} ${plural(days, ['день', 'дня', 'дней'])}`
  return {
    long: `${DAY_MONTH.format(date)}, ${WEEKDAY.format(date)}`,
    day: date.getDate(),
    month: MONTH_SHORT.format(date).replace('.', ''),
    weekday: WEEKDAY_SHORT.format(date),
    relative,
  }
}
