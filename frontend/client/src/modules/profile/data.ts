import { apiRequest } from '@/core/api'
import type { UserRole } from '@/core/session'

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
  /** Точка, от которой считать «находки рядом», — задаётся в «Последнем бое». */
  home_lat?: number | null
  home_lon?: number | null
  /** Значки, выданные сервисами. Старый сервис их не присылает — тогда пусто. */
  achievements?: Achievement[]
  routes_completed?: number
  excursions_completed?: number
  finds_count?: number
  created_at: string
}

export interface Achievement {
  code: string
  earned_at: string
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

/** Лимит `user_service` на фото профиля — `MAX_UPLOAD_BYTES` в `api/routers/uploads.py`. */
export const AVATAR_MAX_MB = 5

/**
 * Фото профиля — в хранилище `user_service`; обратно приходит адрес, который и
 * уходит в `avatar_url`. Хранилище не поднято — ручка отвечает 503, а остальной
 * профиль сохраняется как обычно.
 */
export async function uploadAvatar(file: File): Promise<string> {
  const body = new FormData()
  body.append('file', file)
  const { url } = await apiRequest<{ url: string }>('POST', 'users', '/uploads', { body, auth: true })
  return url
}

/** Ближайший выезд, на который человек записан. */
export function nextTrip(trips: MyTrip[] | null): MyTrip | null {
  const today = new Date().toISOString().slice(0, 10)
  return (trips ?? []).filter((trip) => trip.starts_on >= today).sort((a, b) => a.starts_on.localeCompare(b.starts_on))[0] ?? null
}

/**
 * Значки. Код выдаёт сервис, где случилось событие (`ACHIEVEMENT_TITLES` в
 * user_service); здесь — как их показать и как заслужить.
 */
export const ACHIEVEMENTS: Record<string, { title: string; hint: string; icon: string; tone: string }> = {
  first_route_completed: {
    title: 'Первый маршрут',
    hint: 'Пройдите маршрут до конца',
    icon: 'route',
    tone: 'bg-secondary-container text-on-secondary-container',
  },
  trip_volunteer: {
    title: 'Доброволец',
    hint: 'Съездите с отрядом на выезд',
    icon: 'hiking',
    tone: 'bg-secondary-container text-on-secondary-container',
  },
  archive_helper: {
    title: 'Помощник архива',
    hint: 'Запись, подтверждённая краеведом',
    icon: 'auto_stories',
    tone: 'bg-tertiary-fixed text-on-tertiary-fixed',
  },
  donor: {
    title: 'Жертвователь',
    hint: 'Помогите сбору отряда в «Штабе»',
    icon: 'volunteer_activism',
    tone: 'bg-tertiary-fixed text-on-tertiary-fixed',
  },
}

export interface RoleInfo {
  title: string
  icon: string
  /** Что роль добавляет к тому, что доступно всем. */
  gives: string[]
}

/** Доступно любому с аккаунтом. */
export const EVERYONE_CAN = [
  'Маршруты и квесты для детей',
  'Экскурсии с краеведом',
  '«Живое фото» и народный архив',
  'Выезды и сборы в «Штабе»',
]

/**
 * Роли и что они дают. Списки повторяют правила ядра (`core/session/roles.ts`)
 * и сервисов — меняются там, меняются и здесь.
 */
export const ROLES: Record<UserRole, RoleInfo> = {
  family: { title: 'Семья', icon: 'family_restroom', gives: [] },
  searcher: {
    title: 'Поисковик',
    icon: 'person_search',
    gives: ['Отмечать места «Последнего боя»', 'Заводить отряд, выезды и сборы'],
  },
  local_historian: {
    title: 'Краевед',
    icon: 'history_edu',
    gives: ['Проверять народный архив', 'Отмечать места «Последнего боя»', 'Водить экскурсии', 'Подтверждать исследователей'],
  },
  mentor: {
    title: 'Наставник',
    icon: 'school',
    gives: ['Водить экскурсии', 'Проверять народный архив', 'Подтверждать исследователей'],
  },
  moderator: {
    title: 'Модератор',
    icon: 'shield_person',
    gives: ['Всё, что могут краеведы', 'Вести стадии мест «Последнего боя»', 'Управлять всеми отрядами'],
  },
}

export const ROLE_ORDER: readonly UserRole[] = ['family', 'searcher', 'local_historian', 'mentor', 'moderator']

/** Чужой профиль по номеру жетона — краевед смотрит, кого подтверждает. */
export function fetchProfileById(profileId: string): Promise<Profile> {
  return apiRequest('GET', 'users', `/profiles/${encodeURIComponent(profileId)}`, { auth: true })
}

/** Подтвердить исследователя — краевед, наставник, модератор (`_VERIFIER_ROLES` в user_service). */
export function verifyProfile(profileId: string, isVerified: boolean): Promise<Profile> {
  return apiRequest('PATCH', 'users', `/profiles/${encodeURIComponent(profileId)}/verify`, {
    body: { is_verified: isVerified },
    auth: true,
  })
}

/** Выдать роль — только администратору платформы (`require_root` в auth_service). */
export function setUserRole(userId: string, role: UserRole): Promise<unknown> {
  return apiRequest('PATCH', 'auth', `/admin/users/${encodeURIComponent(userId)}/role`, { body: { role }, auth: true })
}

export interface RoleApplication {
  experience: string
  organization: string
  links: string
}

/**
 * Текст заявки на роль краеведа. Отдельной ручки для заявок в сервисах нет:
 * роль выдаёт администратор платформы, и заявка уходит ему сообщением.
 */
export function applicationText(name: string, userId: string, city: string, application: RoleApplication): string {
  return [
    'Заявка на роль краеведа в «Маршрутах победы»',
    `Имя: ${name}`,
    city ? `Город: ${city}` : '',
    `Номер жетона: ${userId}`,
    application.organization.trim() ? `Музей, школа, организация: ${application.organization.trim()}` : '',
    `Опыт: ${application.experience.trim()}`,
    application.links.trim() ? `Публикации и ссылки: ${application.links.trim()}` : '',
  ]
    .filter(Boolean)
    .join('\n')
}
