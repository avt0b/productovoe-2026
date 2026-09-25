/**
 * HTTP-клиент админки.
 *
 * Знает про пару токенов и умеет ровно одну хитрость: при 401 один раз
 * пробует обновить access-токен и повторить запрос. Параллельные запросы,
 * упавшие в 401, ждут одного общего обновления, а не запускают семь своих.
 */

// Собранная админка живёт на сервере за nginx и ходит в admin_service с того же
// сайта — через /api (location /api/admin/). В dev — напрямую в сервис.
const DEFAULT_BASE_URL = import.meta.env.PROD ? '/api' : 'http://127.0.0.1:8010'
const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? DEFAULT_BASE_URL).replace(/\/$/, '')

const ACCESS_KEY = 'marshruty.admin.access'
const REFRESH_KEY = 'marshruty.admin.refresh'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/** Токены живут в localStorage: перезагрузка страницы не должна разлогинивать. */
function read(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

function write(key: string, value: string | null): void {
  try {
    if (value === null) localStorage.removeItem(key)
    else localStorage.setItem(key, value)
  } catch {
    /* приватный режим — работаем в памяти текущей вкладки */
  }
}

let accessToken: string | null = read(ACCESS_KEY)
let refreshToken: string | null = read(REFRESH_KEY)

export function getAccessToken(): string | null {
  return accessToken
}

export function hasSession(): boolean {
  return Boolean(accessToken && refreshToken)
}

export function setTokens(access: string, refresh: string): void {
  accessToken = access
  refreshToken = refresh
  write(ACCESS_KEY, access)
  write(REFRESH_KEY, refresh)
}

export function clearTokens(): void {
  accessToken = null
  refreshToken = null
  write(ACCESS_KEY, null)
  write(REFRESH_KEY, null)
}

export function getRefreshToken(): string | null {
  return refreshToken
}

/** Вызывается, когда обновиться не удалось — роутер уводит на /login. */
type SessionExpiredHandler = () => void
let onSessionExpired: SessionExpiredHandler = () => undefined

export function setSessionExpiredHandler(handler: SessionExpiredHandler): void {
  onSessionExpired = handler
}

async function parseError(response: Response): Promise<string> {
  try {
    const body = await response.json()
    const detail = (body as { detail?: unknown }).detail
    if (typeof detail === 'string') return detail
    // Ошибка валидации FastAPI: detail — массив объектов.
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: string }
      if (first.msg) return first.msg
    }
  } catch {
    /* тело не JSON */
  }
  if (response.status === 502) return 'Сервис платформы недоступен'
  return `Ошибка ${response.status}`
}

let refreshInFlight: Promise<boolean> | null = null

async function refreshSession(): Promise<boolean> {
  if (!refreshToken) return false
  if (refreshInFlight) return refreshInFlight

  refreshInFlight = (async () => {
    try {
      const response = await fetch(`${BASE_URL}/admin/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })
      if (!response.ok) {
        clearTokens()
        return false
      }
      const pair = (await response.json()) as { access_token: string; refresh_token: string }
      setTokens(pair.access_token, pair.refresh_token)
      return true
    } catch {
      return false
    } finally {
      refreshInFlight = null
    }
  })()

  return refreshInFlight
}

export interface RequestOptions {
  method?: string
  params?: Record<string, string | number | boolean | undefined | null>
  body?: unknown
  /** Для /login и /refresh — запросов, которые сами добывают токен. */
  anonymous?: boolean
}

function buildUrl(path: string, params?: RequestOptions['params']): string {
  const url = new URL(BASE_URL + path, window.location.origin)
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value === undefined || value === null || value === '') continue
      url.searchParams.set(key, String(value))
    }
  }
  return url.toString()
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', params, body, anonymous = false } = options

  const send = async (): Promise<Response> => {
    const headers: Record<string, string> = {}
    if (body !== undefined) headers['Content-Type'] = 'application/json'
    if (!anonymous && accessToken) headers.Authorization = `Bearer ${accessToken}`

    return fetch(buildUrl(path, params), {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  }

  let response: Response
  try {
    response = await send()
  } catch {
    throw new ApiError(0, 'Не удалось связаться с сервером админки')
  }

  if (response.status === 401 && !anonymous) {
    if (await refreshSession()) {
      response = await send()
    } else {
      clearTokens()
      onSessionExpired()
      throw new ApiError(401, 'Сессия истекла — войдите заново')
    }
  }

  if (!response.ok) {
    throw new ApiError(response.status, await parseError(response))
  }

  if (response.status === 204) return undefined as T
  const text = await response.text()
  return (text ? JSON.parse(text) : undefined) as T
}

export const api = {
  get: <T>(path: string, params?: RequestOptions['params']) => request<T>(path, { params }),
  post: <T>(path: string, body?: unknown, params?: RequestOptions['params']) =>
    request<T>(path, { method: 'POST', body, params }),
  patch: <T>(path: string, body?: unknown, params?: RequestOptions['params']) =>
    request<T>(path, { method: 'PATCH', body, params }),
  delete: <T>(path: string, params?: RequestOptions['params']) =>
    request<T>(path, { method: 'DELETE', params }),
}
