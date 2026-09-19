import { ApiError, apiGet, apiRequest, withDemoFallback, type Sourced } from '@/core/api'

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

/** Прогресс семьи по маршруту — какие точки уже пройдены. */
export interface RouteProgress {
  route_id: string
  user_id: string
  completed_waypoint_ids: string[]
  current_index: number
  started_at: string
  completed_at: string | null
}

/**
 * Мой прогресс по маршруту. `null` — маршрут ещё не начат. Нужен аккаунт:
 * прогресс хранит `route_service`, у демо-сессии его нет.
 */
export async function getMyProgress(routeId: string): Promise<RouteProgress | null> {
  try {
    return await apiRequest<RouteProgress>('GET', 'routes', `/routes/${encodeURIComponent(routeId)}/progress/me`, { auth: true })
  } catch (reason) {
    if (reason instanceof ApiError && reason.status === 404) return null
    throw reason
  }
}

/** Отметить точку пройденной. Маршрут начинается сам, если ещё не был начат. */
export function completeWaypoint(routeId: string, waypointId: string): Promise<RouteProgress> {
  return apiRequest('POST', 'routes', `/routes/${encodeURIComponent(routeId)}/progress/complete-waypoint`, {
    body: { waypoint_id: waypointId },
    auth: true,
  })
}
