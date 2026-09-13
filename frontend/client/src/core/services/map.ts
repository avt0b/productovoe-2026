import { apiGet, withDemoFallback, type Sourced } from '@/core/api'

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

/** Сколько точек забирать за раз. Лимит сервиса — 500; для области пока хватает одной страницы. */
const PAGE_LIMIT = 500

function matches(text: string, query: string | undefined): boolean {
  return !query || text.toLowerCase().includes(query.toLowerCase())
}

export function listPoi(query: { kind?: PoiKind; q?: string } = {}): Promise<Sourced<Poi[]>> {
  return withDemoFallback(
    () => apiGet<Poi[]>('map', '/poi', { kind: query.kind, q: query.q, limit: PAGE_LIMIT }),
    () => DEMO_POI.filter((poi) => (!query.kind || poi.kind === query.kind) && matches(poi.title, query.q)),
  )
}

export function listLastStand(query: { status?: LastStandStatus } = {}): Promise<Sourced<LastStandPoint[]>> {
  return withDemoFallback(
    () => apiGet<LastStandPoint[]>('map', '/last-stand', { status: query.status, limit: PAGE_LIMIT }),
    () => DEMO_LAST_STAND.filter((point) => !query.status || point.status === query.status),
  )
}
