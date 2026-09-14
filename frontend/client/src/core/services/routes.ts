import { ApiError, apiGet, withDemoFallback, type Sourced } from '@/core/api'

import { DEMO_ROUTES } from './demoOrel'

/**
 * `route_service`: семейные квест-маршруты и их точки.
 *
 * Типы повторяют pydantic-схемы сервиса (`backend/route_service/api/schemas/route.py`).
 */

export type RouteMode = 'family' | 'general'

export interface RouteSummary {
  id: string
  title: string
  description: string
  mode: RouteMode
  city: string
  distance_km: number
  cover_url: string | null
  created_by: string
  is_published: boolean
  created_at: string
}

export interface Waypoint {
  id: string
  route_id: string
  order_index: number
  title: string
  lat: number
  lon: number
  /** Та же точка на слое «ВОВ» в `map_service`, если есть. */
  poi_id: string | null
  story: string
  kid_task: string
  audio_url: string | null
  ar_hint: string
}

export interface RouteDetail extends RouteSummary {
  waypoints: Waypoint[]
}

export function listRoutes(query: { mode?: RouteMode; city?: string } = {}): Promise<Sourced<RouteSummary[]>> {
  return withDemoFallback(
    () => apiGet<RouteSummary[]>('routes', '/routes', { mode: query.mode, city: query.city, limit: 50 }),
    () =>
      DEMO_ROUTES.filter((route) => (!query.mode || route.mode === query.mode) && (!query.city || route.city === query.city)).map(
        ({ waypoints, ...summary }) => summary,
      ),
  )
}

export function getRoute(id: string): Promise<Sourced<RouteDetail>> {
  return withDemoFallback(
    () => apiGet<RouteDetail>('routes', `/routes/${encodeURIComponent(id)}`),
    () => {
      const route = DEMO_ROUTES.find((item) => item.id === id)
      if (!route) throw new ApiError(404, 'Не нашли — возможно, ссылка устарела')
      return route
    },
  )
}
