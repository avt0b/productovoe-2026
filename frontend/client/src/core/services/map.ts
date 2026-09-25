import { apiGet, apiRequest, withDemoFallback, type Sourced } from '@/core/api'

import { DEMO_LAST_STAND, DEMO_POI } from './demoOrel'

/**
 * `map_service`: слой «ВОВ» (`/poi`) и «Последний бой» (`/last-stand`).
 *
 * Типы повторяют pydantic-схемы сервиса (`backend/map_service/api/schemas`),
 * поля — в snake_case, как в ответе: окна сами решают, что из этого показать.
 */

export type PoiKind = 'grave' | 'battle' | 'monument' | 'hospital' | 'trench' | 'airfield' | 'other'

export interface Poi {
  id: string
  kind: PoiKind
  title: string
  description: string
  lat: number
  lon: number
  event_date: string | null
  date_text: string
  source: string
  created_by: string
  created_at: string
}

export type LastStandStatus = 'discovered' | 'archive_confirmed' | 'remains_raised'

export interface LastStandPoint {
  id: string
  soldier_name: string
  unit: string
  lat: number
  lon: number
  circumstances: string
  death_date: string | null
  date_text: string
  source: string
  status: LastStandStatus
  created_by: string
  created_at: string
}

/** Сколько точек забирать за раз — это лимит сервиса. */
const PAGE_LIMIT = 500

/** Предохранитель от бесконечного цикла, если сервис вдруг перестанет уважать `offset`. */
const MAX_PAGES = 40

/**
 * Весь слой целиком, страница за страницей. Одной страницы не хватает: в
 * Орловской области уже почти девятьсот мест, и без догрузки карта молча
 * теряла всё, что не влезло в первые 500. Между страницами слой могли
 * дополнить — повторы по `id` отбрасываем.
 */
async function fetchAllPages<T extends { id: string }>(load: (offset: number) => Promise<T[]>): Promise<T[]> {
  const byId = new Map<string, T>()
  for (let page = 0; page < MAX_PAGES; page++) {
    const rows = await load(page * PAGE_LIMIT)
    for (const row of rows) if (!byId.has(row.id)) byId.set(row.id, row)
    if (rows.length < PAGE_LIMIT) break
  }
  return [...byId.values()]
}

function matches(text: string, query: string | undefined): boolean {
  return !query || text.toLowerCase().includes(query.toLowerCase())
}

export function listPoi(query: { kind?: PoiKind; q?: string } = {}): Promise<Sourced<Poi[]>> {
  return withDemoFallback(
    () => fetchAllPages((offset) => apiGet<Poi[]>('map', '/poi', { kind: query.kind, q: query.q, limit: PAGE_LIMIT, offset })),
    () => DEMO_POI.filter((poi) => (!query.kind || poi.kind === query.kind) && matches(poi.title, query.q)),
  )
}

export function listLastStand(query: { status?: LastStandStatus } = {}): Promise<Sourced<LastStandPoint[]>> {
  return withDemoFallback(
    () =>
      fetchAllPages((offset) =>
        apiGet<LastStandPoint[]>('map', '/last-stand', { status: query.status, limit: PAGE_LIMIT, offset }),
      ),
    () => DEMO_LAST_STAND.filter((point) => !query.status || point.status === query.status),
  )
}

/**
 * Новая точка слоя «ВОВ».
 *
 * Дополнять слой могут поисковики и краеведы (`_CONTRIBUTOR_ROLES`
 * в `map_service`) — у остальных сервис ответит 403, поэтому кнопку показываем
 * только им (`can.addPoi`).
 */
export interface PoiDraft {
  kind: PoiKind
  title: string
  description: string
  lat: number
  lon: number
  /** Как о дате говорят люди: «5 августа 1943», «октябрь 1941 — август 1943». */
  date_text: string
  /** Откуда сведения: Книга Памяти, музей, рассказ жителя. */
  source: string
}

export function createPoi(draft: PoiDraft): Promise<Poi> {
  return apiRequest('POST', 'map', '/poi', { body: draft, auth: true })
}

/** Поправить точку — её автор или администратор (`_ensure_can_edit` в map_service). */
export function updatePoi(poiId: string, patch: Partial<PoiDraft>): Promise<Poi> {
  return apiRequest('PATCH', 'map', `/poi/${encodeURIComponent(poiId)}`, { body: patch, auth: true })
}

/** Убрать точку со слоя — тоже только автор или администратор. */
export function deletePoi(poiId: string): Promise<void> {
  return apiRequest('DELETE', 'map', `/poi/${encodeURIComponent(poiId)}`, { auth: true })
}
