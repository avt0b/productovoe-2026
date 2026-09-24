import { serviceBaseUrl, type ServiceName } from './server'

/**
 * Запросы к публичным сервисам.
 *
 * Адрес каждого сервиса — `core/server.ts`: из сборки (`.env.local`). Для APK
 * на телефоне нужен адрес компьютера в локальной сети: `127.0.0.1` на
 * телефоне — сам телефон.
 */

export type { ServiceName } from './server'

/** Дольше спиннер на телефоне никто не ждёт — лучше показать демо и честно сказать об этом. */
const TIMEOUT_MS = 6000

/**
 * Загрузка файла — отдельный разговор: снимок на несколько мегабайт по
 * мобильной сети в шесть секунд не уходит, а обрыв на полпути выглядел бы как
 * «сервис недоступен».
 */
const UPLOAD_TIMEOUT_MS = 45_000

/**
 * Сколько помнить, что сервис не ответил. Иначе каждый следующий экран снова
 * ждал бы таймаут, прежде чем показать демо-данные.
 *
 * Ключ — адрес сервиса, а не имя: сменили сервер — старые отказы не мешают новому.
 */
const DOWN_MEMORY_MS = 30_000
const downUntil = new Map<string, number>()

/** Сервис не ответил вовсе: нет сети, сервер не запущен, истёк таймаут. */
export class ServiceUnavailableError extends Error {
  constructor(readonly service: ServiceName) {
    super('Сервис недоступен — проверьте подключение к интернету')
    this.name = 'ServiceUnavailableError'
  }
}

/** Сервис ответил, но ошибкой. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export type QueryParams = Record<string, string | number | boolean | null | undefined>

export type HttpMethod = 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE'

export interface RequestOptions {
  query?: QueryParams
  /** Тело запроса. Объект уходит JSON, `FormData` — как multipart. */
  body?: unknown
  /** Запрос от имени человека: подставить токен сессии, при 401 — обновить токен и повторить. */
  auth?: boolean
  /** Явный токен — когда его ещё нет в сессии (сразу после входа). */
  token?: string
}

/**
 * Откуда запросы берут токен. Регистрирует сессия (`core/session/store.ts`):
 * так `api.ts` не импортирует сессию, а сессия — `api.ts`, без кругового импорта.
 */
export interface AuthHandlers {
  accessToken(): string | null
  /** Когда истекает access-токен, мс unix-времени. `null` — токена нет. */
  expiresAt(): number | null
  /** Обновить токен. `true` — получилось, запрос можно повторить. */
  refresh(): Promise<boolean>
}

/**
 * Токен обновляем заранее, а не по 401: запрос с просроченным токеном браузер
 * показывает в консоли красной ошибкой, хотя ничего не сломалось.
 */
const REFRESH_AHEAD_MS = 30_000

let authHandlers: AuthHandlers | null = null

export function setAuthHandlers(handlers: AuthHandlers): void {
  authHandlers = handlers
}

export function apiGet<T>(service: ServiceName, path: string, query: QueryParams = {}): Promise<T> {
  return apiRequest<T>('GET', service, path, { query })
}

export async function apiRequest<T>(
  method: HttpMethod,
  service: ServiceName,
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  if (options.auth && !options.token) await refreshIfExpiring()

  let response = await send(method, service, path, options)

  // access-токен живёт 15 минут: истёк — обновляем один раз и повторяем запрос.
  if (response.status === 401 && options.auth && !options.token && authHandlers && (await authHandlers.refresh())) {
    response = await send(method, service, path, options)
  }

  if (!response.ok) throw new ApiError(response.status, await errorMessage(response))
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

async function refreshIfExpiring(): Promise<void> {
  const expiresAt = authHandlers?.expiresAt() ?? null
  if (authHandlers && expiresAt !== null && expiresAt - Date.now() < REFRESH_AHEAD_MS) await authHandlers.refresh()
}

/**
 * Поток событий от сервиса (Server-Sent Events) от имени человека. Тело читает
 * вызывающий, таймаута нет: поток живёт, пока открыт экран, и закрывается
 * через `signal`. `EventSource` тут не годится — он не передаёт заголовок
 * `Authorization`, а токен в адресе осел бы в журналах шлюза.
 */
export async function apiStream(service: ServiceName, path: string, signal: AbortSignal): Promise<Response> {
  await refreshIfExpiring()
  const token = authHandlers?.accessToken()
  if (!token) throw new ApiError(401, 'Нужно войти по почте и паролю')
  let response: Response
  try {
    response = await fetch(`${serviceBaseUrl(service)}${path}`, {
      headers: { Accept: 'text/event-stream', Authorization: `Bearer ${token}` },
      signal,
    })
  } catch (reason) {
    if (signal.aborted) throw reason
    throw new ServiceUnavailableError(service)
  }
  if (!response.ok) throw new ApiError(response.status, await errorMessage(response))
  return response
}

async function send(method: HttpMethod, service: ServiceName, path: string, options: RequestOptions): Promise<Response> {
  const base = serviceBaseUrl(service)
  if ((downUntil.get(base) ?? 0) > Date.now()) throw new ServiceUnavailableError(service)

  const url = new URL(`${base}${path}`)
  for (const [key, value] of Object.entries(options.query ?? {})) {
    if (value !== null && value !== undefined) url.searchParams.set(key, String(value))
  }

  const headers: Record<string, string> = { Accept: 'application/json' }
  // FormData уходит как есть: заголовок с `boundary` проставляет сам браузер,
  // а заданный вручную `Content-Type` сломал бы разбор на сервере.
  const multipart = options.body instanceof FormData
  if (options.body !== undefined && !multipart) headers['Content-Type'] = 'application/json'

  const token = options.token ?? (options.auth ? authHandlers?.accessToken() : null)
  if (options.auth && !token) throw new ApiError(401, 'Нужно войти по почте и паролю')
  if (token) headers.Authorization = `Bearer ${token}`

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), multipart ? UPLOAD_TIMEOUT_MS : TIMEOUT_MS)
  try {
    return await fetch(url, {
      method,
      headers,
      body: options.body === undefined ? undefined : multipart ? (options.body as FormData) : JSON.stringify(options.body),
      signal: controller.signal,
    })
  } catch (reason) {
    // Сюда же попадает отказ CORS — в консоли видно, куда именно не достучались.
    console.warn(`[api] ${service}: нет ответа от ${url.origin}`, reason)
    // Сорвавшаяся загрузка файла — не повод считать весь сервис лежачим: чаще
    // всего это тяжёлый снимок или хранилище, а профиль и списки работают.
    if (!multipart) downUntil.set(base, Date.now() + DOWN_MEMORY_MS)
    throw new ServiceUnavailableError(service)
  } finally {
    clearTimeout(timer)
  }
}

/**
 * Служебные ответы самого FastAPI — по-английски и не о деле: так отвечает
 * сервис, до которого запрос дошёл, но ручки такой у него нет. Показывать их
 * человеку незачем — ниже для каждого кода есть свои слова.
 */
const FRAMEWORK_DETAILS = new Set(['Not Found', 'Method Not Allowed', 'Internal Server Error', 'Unauthorized', 'Forbidden'])

async function errorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown } | null
    if (typeof body?.detail === 'string' && body.detail && !FRAMEWORK_DETAILS.has(body.detail)) return body.detail
    // 422 от pydantic: в detail — список полей с ошибками.
    if (Array.isArray(body?.detail)) return 'Проверьте введённые данные'
  } catch {
    // Тело не JSON — хватит кода ответа.
  }
  if (response.status === 401) return 'Сессия истекла — войдите снова'
  if (response.status === 403) return 'Здесь нужны права другой роли'
  if (response.status === 404) return 'Не нашли — возможно, ссылка устарела или сервис ещё не обновлён'
  if (response.status >= 500) return 'Сервис ответил ошибкой — попробуйте позже'
  return `Сервис ответил ошибкой ${response.status}`
}

/** Откуда пришли данные экрана. */
export type DataSource = 'live' | 'demo'

export interface Sourced<T> {
  data: T
  source: DataSource
}

/**
 * Данные из сервиса, а если сервис не ответил — демо-набор модуля.
 *
 * Так карта работает и без поднятого бэкенда: на защите, в APK без сети.
 * Экран обязан показать, что данные демо (`source`, `<DemoDataBadge>`).
 * Ошибку, которой сервис *ответил*, демо не прячет: она остаётся ошибкой.
 */
export async function withDemoFallback<T>(load: () => Promise<T>, demo: () => T): Promise<Sourced<T>> {
  try {
    return { data: await load(), source: 'live' }
  } catch (reason) {
    if (reason instanceof ServiceUnavailableError) return { data: demo(), source: 'demo' }
    throw reason
  }
}
