import { SERVICE_NAMES, resolveServiceUrl, type ServerChoice, type ServiceName } from '@/core/server'

/** Результат проверки одного сервиса. */
export interface ProbeResult {
  service: ServiceName
  url: string
  state: 'ok' | 'error' | 'down'
  /** Время ответа, мс. */
  ms: number | null
  detail: string
}

const TIMEOUT_MS = 4000

/**
 * Чем проверять, что сервис жив. У `auth` через шлюз `/health` не проходит —
 * префикс `/api` ведёт на его ручки `/auth/*`, — поэтому у него открытый список
 * способов входа.
 */
function probePath(service: ServiceName): string {
  return service === 'auth' ? '/auth/external/providers' : '/health'
}

async function probe(choice: ServerChoice, service: ServiceName): Promise<ProbeResult> {
  const url = resolveServiceUrl(choice, service)
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)
  const startedAt = performance.now()
  try {
    const response = await fetch(`${url}${probePath(service)}`, { signal: controller.signal })
    const ms = Math.round(performance.now() - startedAt)
    return response.ok
      ? { service, url, state: 'ok', ms, detail: `${ms} мс` }
      : { service, url, state: 'error', ms, detail: `ответил ${response.status}` }
  } catch {
    // Браузер не различает «не запущен» и «не пустил CORS» — обе причины в подсказке экрана.
    return { service, url, state: 'down', ms: null, detail: 'нет ответа' }
  } finally {
    clearTimeout(timer)
  }
}

/** Проверить все сервисы разом. */
export function probeAll(choice: ServerChoice): Promise<ProbeResult[]> {
  return Promise.all(SERVICE_NAMES.map((service) => probe(choice, service)))
}

const RECENT_KEY = 'marshruty.client.server.recent'
const RECENT_LIMIT = 4

/** Недавние адреса — чтобы не набирать IP каждый раз заново. */
export function readRecent(): string[] {
  try {
    const parsed: unknown = JSON.parse(localStorage.getItem(RECENT_KEY) ?? '[]')
    return Array.isArray(parsed) ? parsed.filter((item): item is string => typeof item === 'string') : []
  } catch {
    return []
  }
}

export function rememberRecent(origin: string): void {
  try {
    const next = [origin, ...readRecent().filter((item) => item !== origin)].slice(0, RECENT_LIMIT)
    localStorage.setItem(RECENT_KEY, JSON.stringify(next))
  } catch {
    /* приватный режим — без истории */
  }
}
