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
  /** Семейное древо — приходит вместе с профилем, отдельный запрос не нужен. */
  heroes?: FamilyHero[]
  routes_completed?: number
  excursions_completed?: number
  finds_count?: number
  created_at: string
}

export interface Achievement {
  code: string
  earned_at: string
}

/** Судьба героя семейного древа — как `HeroStatus` в user_service. */
export type HeroStatus = 'killed_in_action' | 'missing_in_action' | 'died_of_wounds' | 'veteran'

export interface FamilyHero {
  id: string
  owner_id: string
  name: string
  status: HeroStatus
  birth_year: number | null
  death_year: number | null
  unit: string
  note: string
  photo_url: string | null
  /** Карточка бойца в народном архиве, если она заведена. */
  archive_entry_id: string | null
  created_at: string
}

export type HeroDraft = Omit<FamilyHero, 'id' | 'owner_id' | 'created_at'>

/** Как подписываем судьбу героя. Порядок — от «дожил» к «пропал без вести». */
export const HERO_STATUS: Record<HeroStatus, { title: string; icon: string; tone: string }> = {
  veteran: { title: 'Дожил до Победы', icon: 'military_tech', tone: 'bg-secondary-container text-on-secondary-container' },
  killed_in_action: { title: 'Погиб в бою', icon: 'local_florist', tone: 'bg-tertiary-fixed text-on-tertiary-fixed' },
  died_of_wounds: { title: 'Умер от ран', icon: 'local_hospital', tone: 'bg-tertiary-fixed text-on-tertiary-fixed' },
  missing_in_action: { title: 'Пропал без вести', icon: 'person_search', tone: 'bg-surface-container-high text-on-surface-variant' },
}

export const HERO_STATUS_ORDER: readonly HeroStatus[] = [
  'veteran',
  'killed_in_action',
  'died_of_wounds',
  'missing_in_action',
]

/** Семейное древо: его ведёт сам человек, чужие герои никому не видны. */
export function createHero(draft: HeroDraft): Promise<FamilyHero> {
  return apiRequest('POST', 'users', '/family-heroes', { body: draft, auth: true })
}

export function updateHero(heroId: string, patch: Partial<HeroDraft>): Promise<FamilyHero> {
  return apiRequest('PATCH', 'users', `/family-heroes/${encodeURIComponent(heroId)}`, { body: patch, auth: true })
}

export function deleteHero(heroId: string): Promise<void> {
  return apiRequest('DELETE', 'users', `/family-heroes/${encodeURIComponent(heroId)}`, { auth: true })
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

/** Отряд, музей или школа из «Штаба» — для настроек профиля и заявки на роль. */
export interface SquadOption {
  id: string
  name: string
  /** Нет у старого сервиса — тогда это отряд. */
  kind?: string
  region?: string
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
 *
 * Ролей три. Четвёртая по продукту — администратор платформы: это не роль, а
 * флаг `is_root`, и в приложении он только снимает ограничения, отдельной
 * карточки у него нет (админка — это веб).
 */
export const ROLES: Record<UserRole, RoleInfo> = {
  family: { title: 'Семья', icon: 'family_restroom', gives: [] },
  searcher: {
    title: 'Поисковик',
    icon: 'person_search',
    gives: ['Отмечать места «Последнего боя»', 'Заводить отряд, выезды и сборы', 'Проверять народный архив'],
  },
  local_historian: {
    title: 'Краевед',
    icon: 'history_edu',
    gives: ['Проверять народный архив', 'Отмечать места «Последнего боя»', 'Водить экскурсии'],
  },
}

export const ROLE_ORDER: readonly UserRole[] = ['family', 'searcher', 'local_historian']

/** Чужой профиль по номеру жетона — краевед смотрит, кого подтверждает. */
export function fetchProfileById(profileId: string): Promise<Profile> {
  return apiRequest('GET', 'users', `/profiles/${encodeURIComponent(profileId)}`, { auth: true })
}

/** Подтвердить исследователя — только администратор (`set_verified` требует `is_root`). */
export function verifyProfile(profileId: string, isVerified: boolean): Promise<Profile> {
  return apiRequest('PATCH', 'users', `/profiles/${encodeURIComponent(profileId)}/verify`, {
    body: { is_verified: isVerified },
    auth: true,
  })
}

/**
 * Заявка на роль.
 *
 * Роли выдаёт только администратор платформы (`require_root` в `auth_service`),
 * и очереди заявок в сервисах нет — ни ручки, ни таблицы. Поэтому заявка
 * собирается здесь, уходит администратору сообщением, а её след остаётся на
 * устройстве: приложение помнит, что человек уже подавался, и не даёт собирать
 * всё заново. Появится ручка — сюда встанет обычный `apiRequest`.
 */

export interface DocumentKind {
  id: string
  title: string
}

export interface RequestableRole {
  role: UserRole
  /** Кому роль, человеческим языком: «музейщикам, учителям, краеведам». */
  who: string
  /** Чем подтверждают, что человек тот, за кого себя выдаёт. */
  documents: readonly DocumentKind[]
}

/** На что можно подать заявку — `REQUESTABLE_ROLES` в user_service. */
export const REQUESTABLE_ROLES: readonly RequestableRole[] = [
  {
    role: 'local_historian',
    who: 'Учителям, музейщикам, членам краеведческих обществ',
    documents: [
      { id: 'membership', title: 'Членский билет краеведческого общества' },
      { id: 'diploma', title: 'Диплом или документ об образовании' },
      { id: 'work', title: 'Справка с места работы: музей, школа, архив' },
      { id: 'other', title: 'Другой документ' },
    ],
  },
  {
    role: 'searcher',
    who: 'Участникам поисковых отрядов и «Вахты Памяти»',
    documents: [
      { id: 'squad', title: 'Удостоверение поискового отряда' },
      { id: 'certificate', title: 'Сертификат участника «Вахты Памяти»' },
      { id: 'order', title: 'Приказ или выписка о зачислении в отряд' },
      { id: 'other', title: 'Другой документ' },
    ],
  },
]

/** Лимит `media_service` на файл — 15 МБ, как у фото в «Живой памяти». */
export const DOCUMENT_MAX_MB = 15

/**
 * Семейные связи — живые люди, которые хотят находить друг друга: родитель и
 * ребёнок на маршруте, бабушка и внук. Не путать с «Героями семьи»: там
 * приватное древо погибших, здесь — учётные записи платформы.
 *
 * Связь заводится по короткому коду: один код — одно использование, семь дней.
 */
export interface FamilyMember {
  member_id: string
  display_name: string
  city: string
  avatar_url: string | null
  home_lat: number | null
  home_lon: number | null
  linked_at: string
}

export interface FamilyInvite {
  code: string
  expires_at: string
}

export function familyMembers(): Promise<FamilyMember[]> {
  return apiRequest('GET', 'users', '/family-links/mine', { auth: true })
}

export function createFamilyInvite(): Promise<FamilyInvite> {
  return apiRequest('POST', 'users', '/family-links/invite', { auth: true })
}

/** Ввести чужой код. Сервис отвечает 409 на свой, использованный и просроченный. */
export function redeemFamilyInvite(code: string): Promise<void> {
  return apiRequest('POST', 'users', '/family-links/redeem', { body: { code: code.trim().toUpperCase() }, auth: true })
}

/** Разорвать связь — сразу с обеих сторон, как и заводилась. */
export function removeFamilyMember(memberId: string): Promise<void> {
  return apiRequest('DELETE', 'users', `/family-links/${encodeURIComponent(memberId)}`, { auth: true })
}

/** Решение по заявке — `ApplicationStatus` в user_service. */
export type ApplicationStatus = 'pending' | 'approved' | 'rejected'

/** Заявка на роль, как её хранит user_service. */
export interface RoleApplication {
  id: string
  user_id: string
  requested_role: UserRole
  full_name: string
  contact: string
  evidence: string
  evidence_url: string | null
  status: ApplicationStatus
  review_note: string
  reviewed_by: string | null
  created_at: string
}

export interface RoleApplicationDraft {
  requested_role: 'searcher' | 'local_historian'
  full_name: string
  /** Телефон, телеграм — как администратору связаться. Свободный текст. */
  contact: string
  /** Опыт и доказательства одним текстом: сервис не разбирает его на графы. */
  evidence: string
  evidence_url: string | null
}

/**
 * Мои заявки — все, вместе с рассмотренными: отказ с причиной человеку нужен
 * не меньше одобрения.
 */
export function myRoleApplications(): Promise<RoleApplication[]> {
  return apiRequest('GET', 'users', '/role-applications/mine', { auth: true })
}

/**
 * Подать заявку. Сервис отвечает 409, если роль уже есть или заявка на неё
 * ещё на рассмотрении, — повторную подачу он не примет.
 */
export function submitRoleApplication(draft: RoleApplicationDraft): Promise<RoleApplication> {
  return apiRequest('POST', 'users', '/role-applications', { body: draft, auth: true })
}

/** Снимок документа — в хранилище `media_service`; в заявку уходит адрес. */
export async function uploadRoleDocument(file: File): Promise<string> {
  const body = new FormData()
  body.append('file', file)
  const { url } = await apiRequest<{ url: string }>('POST', 'media', '/uploads', { body, auth: true })
  return url
}
