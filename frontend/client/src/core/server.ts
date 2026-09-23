import { readonly, ref } from 'vue'

/**
 * Куда приложение ходит за данными.
 *
 * По умолчанию — адреса из сборки (`.env.local`, `.env.android.local`). Пока идут
 * тесты, сервер можно сменить прямо в приложении (модуль `server`, экран
 * «Сервер»): выбор хранится на устройстве и перекрывает адреса сборки. Убрать
 * модуль — останутся только адреса сборки, этот файл менять не придётся.
 */

export type ServiceName = 'auth' | 'users' | 'map' | 'hq' | 'archive' | 'routes' | 'media'

export const SERVICE_NAMES: readonly ServiceName[] = ['auth', 'users', 'map', 'hq', 'archive', 'routes', 'media']

/**
 * - `ports` — сервисы подняты по отдельности, каждый на своём порту (локальная разработка);
 * - `gateway` — один адрес, сервисы за шлюзом под `/api/<сервис>`.
 */
export type ServerMode = 'ports' | 'gateway'

export interface ServerChoice {
  mode: ServerMode
  /** Адрес компьютера или шлюза: `http://192.168.1.10`, `https://marshruty.ru`. */
  origin: string
}

/** Порты сервисов — `backend/README.md`. */
export const SERVICE_PORTS: Record<ServiceName, number> = {
  auth: 8001,
  users: 8002,
  map: 8003,
  hq: 8004,
  archive: 8005,
  routes: 8006,
  media: 8007,
}

/**
 * Префиксы шлюза — те же, что у прокси веб-версии (`frontend/web/vite.config.js`).
 * У `auth` префикс короче: его ручки сами начинаются с `/auth`.
 */
const GATEWAY_PREFIXES: Record<ServiceName, string> = {
  auth: '/api',
  users: '/api/users',
  map: '/api/map',
  hq: '/api/search-hq',
  archive: '/api/archive',
  routes: '/api/routes',
  media: '/api/media',
}

export const SERVICE_TITLES: Record<ServiceName, string> = {
  auth: 'Вход (auth_service)',
  users: 'Профили (user_service)',
  map: 'Карта (map_service)',
  hq: 'Штаб и экскурсии (search_hq_service)',
  archive: 'Народный архив (archive_service)',
  routes: 'Маршруты (route_service)',
  media: 'Живое фото (media_service)',
}

function trimSlash(value: string): string {
  return value.replace(/\/+$/, '')
}

/** Адреса из сборки. Без `.env.local` — сервисы на этом же компьютере. */
const BUILD_URLS: Record<ServiceName, string> = {
  auth: trimSlash(import.meta.env.VITE_AUTH_API_URL || 'http://127.0.0.1:8001'),
  users: trimSlash(import.meta.env.VITE_USER_API_URL || 'http://127.0.0.1:8002'),
  map: trimSlash(import.meta.env.VITE_MAP_API_URL || 'http://127.0.0.1:8003'),
  hq: trimSlash(import.meta.env.VITE_HQ_API_URL || 'http://127.0.0.1:8004'),
  archive: trimSlash(import.meta.env.VITE_ARCHIVE_API_URL || 'http://127.0.0.1:8005'),
  routes: trimSlash(import.meta.env.VITE_ROUTE_API_URL || 'http://127.0.0.1:8006'),
  media: trimSlash(import.meta.env.VITE_MEDIA_API_URL || 'http://127.0.0.1:8007'),
}

/**
 * Привести введённый адрес к origin: `192.168.1.10` → `http://192.168.1.10`.
 * `null` — адрес не разобрать.
 */
export function normalizeOrigin(input: string): string | null {
  const raw = input.trim()
  if (!raw) return null
  try {
    const url = new URL(/^[a-z][a-z\d+.-]*:\/\//i.test(raw) ? raw : `http://${raw}`)
    if (url.protocol !== 'http:' && url.protocol !== 'https:') return null
    return trimSlash(`${url.protocol}//${url.host}${url.pathname}`)
  } catch {
    return null
  }
}

/** Адрес сервиса при выбранном сервере. */
export function resolveServiceUrl(choice: ServerChoice, service: ServiceName): string {
  if (choice.mode === 'gateway') return `${trimSlash(choice.origin)}${GATEWAY_PREFIXES[service]}`
  // Порт и путь из введённого адреса не нужны: у каждого сервиса свой порт.
  const url = new URL(choice.origin)
  return `${url.protocol}//${url.hostname}:${SERVICE_PORTS[service]}`
}

const STORAGE_KEY = 'marshruty.client.server'

function isChoice(value: unknown): value is ServerChoice {
  const candidate = value as Partial<ServerChoice> | null
  return (
    !!candidate &&
    (candidate.mode === 'ports' || candidate.mode === 'gateway') &&
    typeof candidate.origin === 'string' &&
    normalizeOrigin(candidate.origin) !== null
  )
}

function readStored(): ServerChoice | null {
  try {
    const parsed: unknown = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? 'null')
    return isChoice(parsed) ? parsed : null
  } catch {
    return null
  }
}

const choice = ref<ServerChoice | null>(readStored())

/** Выбранный в приложении сервер. `null` — адреса сборки. */
export const serverChoice = readonly(choice)

/**
 * Сменить сервер. `null` — вернуться к адресам сборки.
 *
 * Сессию меняющий должен закрыть сам и заранее: токены одного сервера на
 * другом недействительны.
 */
export function setServerChoice(next: ServerChoice | null): void {
  choice.value = next
  try {
    if (next) localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
    else localStorage.removeItem(STORAGE_KEY)
  } catch {
    /* приватный режим — выбор проживёт до закрытия вкладки */
  }
}

/** Адрес сервиса, по которому сейчас идут запросы. */
export function serviceBaseUrl(service: ServiceName): string {
  return choice.value ? resolveServiceUrl(choice.value, service) : BUILD_URLS[service]
}

/** Короткая подпись текущего сервера — для экрана входа. */
export function serverLabel(): string {
  if (!choice.value) return `${new URL(BUILD_URLS.auth).hostname} · из сборки`
  const host = new URL(choice.value.origin).host
  return `${host} · ${choice.value.mode === 'ports' ? 'порты' : 'шлюз'}`
}
