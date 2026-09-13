/**
 * Запросы к публичным сервисам.
 *
 * Общего шлюза пока нет — у каждого сервиса свой адрес. Адреса задаются в
 * `.env.local` (`VITE_MAP_API_URL`, `VITE_ROUTE_API_URL`), без них берутся
 * локальные порты из `backend/README.md`. Для APK на телефоне нужен адрес
 * компьютера в локальной сети: `127.0.0.1` на телефоне — сам телефон.
 */

export type ServiceName = 'map' | 'routes'

function baseUrl(value: string | undefined, fallback: string): string {
  return (value || fallback).replace(/\/+$/, '')
}

const BASE_URLS: Record<ServiceName, string> = {
  map: baseUrl(import.meta.env.VITE_MAP_API_URL, 'http://127.0.0.1:8003'),
  routes: baseUrl(import.meta.env.VITE_ROUTE_API_URL, 'http://127.0.0.1:8006'),
}

/** Дольше спиннер на телефоне никто не ждёт — лучше показать демо и честно сказать об этом. */
const TIMEOUT_MS = 6000

/**
 * Сколько помнить, что сервис не ответил. Иначе каждый следующий экран снова
 * ждал бы таймаут, прежде чем показать демо-данные.
 */
const DOWN_MEMORY_MS = 30_000
const downUntil: Partial<Record<ServiceName, number>> = {}

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

export async function apiGet<T>(service: ServiceName, path: string, query: QueryParams = {}): Promise<T> {
  if ((downUntil[service] ?? 0) > Date.now()) throw new ServiceUnavailableError(service)

  const url = new URL(`${BASE_URLS[service]}${path}`)
  for (const [key, value] of Object.entries(query)) {
    if (value !== null && value !== undefined) url.searchParams.set(key, String(value))
  }

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)
  let response: Response
  try {
    response = await fetch(url, { headers: { Accept: 'application/json' }, signal: controller.signal })
  } catch (reason) {
    // Сюда же попадает отказ CORS — в консоли видно, куда именно не достучались.
    console.warn(`[api] ${service}: нет ответа от ${url.origin}`, reason)
    downUntil[service] = Date.now() + DOWN_MEMORY_MS
    throw new ServiceUnavailableError(service)
  } finally {
    clearTimeout(timer)
  }

  if (!response.ok) throw new ApiError(response.status, await errorMessage(response))
  return (await response.json()) as T
}

async function errorMessage(response: Response): Promise<string> {
  if (response.status === 404) return 'Не нашли — возможно, ссылка устарела'
  try {
    const body = (await response.json()) as { detail?: unknown } | null
    if (typeof body?.detail === 'string' && body.detail) return body.detail
  } catch {
    // Тело не JSON — хватит кода ответа.
  }
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
