import { apiRequest } from '@/core/api'

/**
 * Данные окна «Профиль».
 *
 * Сам профиль — `user_service` (`/profiles/me`: имя, город, о себе, отряд,
 * гео-оповещения). Счётчики и «герои семьи» собираются из того, что человек
 * сделал в других сервисах: выезды и экскурсии (`search_hq_service`), записи
 * народного архива (`archive_service`). Любой из них не ответил — его счётчик
 * показывает прочерк, профиль остаётся рабочим.
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
  created_at: string
}

export type ProfilePatch = Partial<
  Pick<Profile, 'display_name' | 'city' | 'bio' | 'avatar_url' | 'squad_id' | 'subscribed_to_search' | 'alert_radius_km'>
>

export type EntryStatus = 'pending' | 'verified' | 'rejected'

export interface MyEntry {
  id: string
  kind: 'event' | 'soldier_card' | 'memory' | 'photo_story'
  title: string
  date_text: string
  status: EntryStatus
  created_at: string
}

export interface MyTrip {
  id: string
  title: string
  location: string
  starts_on: string
}

/** Счётчик на карточке исследователя. */
export interface HeroCounter {
  /** `null` — сервис не ответил. */
  value: number | null
  label: string
  accent?: boolean
}

export interface SquadOption {
  id: string
  name: string
}

export interface ProfileOverview {
  profile: Profile
  /** `null` — сервис не ответил, счётчик неизвестен. */
  trips: MyTrip[] | null
  entries: MyEntry[] | null
  excursions: number | null
  squads: SquadOption[]
}

/** Необязательная часть профиля: не ответила — прочерк, а не ошибка всего экрана. */
async function optional<T>(load: () => Promise<T>): Promise<T | null> {
  try {
    return await load()
  } catch {
    return null
  }
}

export async function fetchProfile(): Promise<ProfileOverview> {
  const [profile, trips, entries, excursions, squads] = await Promise.all([
    // Сервис сам создаёт пустой профиль при первом обращении.
    apiRequest<Profile>('GET', 'users', '/profiles/me', { auth: true }),
    optional(() => apiRequest<MyTrip[]>('GET', 'hq', '/trips/mine', { query: { upcoming_only: false }, auth: true })),
    optional(() => apiRequest<MyEntry[]>('GET', 'archive', '/entries/mine', { auth: true })),
    optional(async () => {
      const mine = await apiRequest<{ guiding: unknown[]; joined: unknown[] }>('GET', 'hq', '/excursions/mine', { auth: true })
      return mine.guiding.length + mine.joined.length
    }),
    optional(() => apiRequest<SquadOption[]>('GET', 'hq', '/squads')),
  ])
  return { profile, trips, entries, excursions, squads: squads ?? [] }
}

export function updateProfile(patch: ProfilePatch): Promise<Profile> {
  return apiRequest('PUT', 'users', '/profiles/me', { body: patch, auth: true })
}

/** Ближайший выезд, на который человек записан. */
export function nextTrip(trips: MyTrip[] | null): MyTrip | null {
  const today = new Date().toISOString().slice(0, 10)
  return (trips ?? []).filter((trip) => trip.starts_on >= today).sort((a, b) => a.starts_on.localeCompare(b.starts_on))[0] ?? null
}
