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
  /** У точки есть эталонный ответ на загадку. Сам ответ сервис не отдаёт — это спойлер. */
  has_answer?: boolean
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

/**
 * Маршруты краеведа: черновики, точки, публикация.
 *
 * Вести маршруты может краевед (`AUTHOR_ROLES` в
 * `route_service`) — у остальных сервис ответит 403, поэтому экраны редактора
 * показываем только тем, кому можно (`can.authorRoute`).
 */

export interface RouteDraft {
  title: string
  description: string
  mode: RouteMode
  city: string
  distance_km: number
  /** Обложка маршрута. `null` — без снимка. */
  cover_url?: string | null
}

/** Черновик по точкам слоя «ВОВ» рядом — «автоматически строить квест-маршруты» из ТЗ. */
export interface AutoRouteDraft {
  lat: number
  lon: number
  radius_km: number
  max_points: number
  title: string
  mode: RouteMode
  city: string
}

export interface WaypointDraft {
  title: string
  lat: number
  lon: number
  poi_id?: string | null
  story: string
  kid_task: string
  ar_hint: string
  /** Эталонный ответ на загадку. Пустой — задание без проверки. */
  expected_answer: string
  /** Аудиорассказ на точке — «аудиовоспоминания» из ТЗ. `null` — только текст. */
  audio_url?: string | null
}

/** Мои маршруты — и опубликованные, и черновики. */
export function listMyRoutes(): Promise<RouteSummary[]> {
  return apiRequest('GET', 'routes', '/routes/mine', { auth: true })
}

export function createRoute(draft: RouteDraft): Promise<RouteSummary> {
  return apiRequest('POST', 'routes', '/routes', { body: draft, auth: true })
}

export function autoGenerateRoute(draft: AutoRouteDraft): Promise<RouteDetail> {
  return apiRequest('POST', 'routes', '/routes/auto-generate', { body: draft, auth: true })
}

export function updateRoute(routeId: string, patch: Partial<RouteDraft>): Promise<RouteSummary> {
  return apiRequest('PATCH', 'routes', `/routes/${encodeURIComponent(routeId)}`, { body: patch, auth: true })
}

/** Опубликовать или снять с публикации. Без точек сервис публиковать не даст. */
export function publishRoute(routeId: string, isPublished: boolean): Promise<RouteSummary> {
  return apiRequest('POST', 'routes', `/routes/${encodeURIComponent(routeId)}/publish`, {
    body: { is_published: isPublished },
    auth: true,
  })
}

export function deleteRoute(routeId: string): Promise<void> {
  return apiRequest('DELETE', 'routes', `/routes/${encodeURIComponent(routeId)}`, { auth: true })
}

/** Маршрут целиком, включая черновик автора: сервис отдаёт его только автору и администратору. */
export function getMyRoute(routeId: string): Promise<RouteDetail> {
  return apiRequest('GET', 'routes', `/routes/${encodeURIComponent(routeId)}`, { auth: true })
}

export function addWaypoint(routeId: string, draft: WaypointDraft): Promise<Waypoint> {
  return apiRequest('POST', 'routes', `/routes/${encodeURIComponent(routeId)}/waypoints`, { body: draft, auth: true })
}

export function updateWaypoint(waypointId: string, patch: Partial<WaypointDraft> & { order_index?: number }): Promise<Waypoint> {
  return apiRequest('PATCH', 'routes', `/waypoints/${encodeURIComponent(waypointId)}`, { body: patch, auth: true })
}

export function deleteWaypoint(waypointId: string): Promise<void> {
  return apiRequest('DELETE', 'routes', `/waypoints/${encodeURIComponent(waypointId)}`, { auth: true })
}

/** Лимит `route_service` на файл — `MAX_UPLOAD_BYTES` в `api/routers/uploads.py`. */
export const ROUTE_FILE_MAX_MB = 20

/**
 * Обложка маршрута или аудио точки — в хранилище `route_service`; обратно
 * приходит адрес. Сервис принимает JPEG/PNG/WebP и MP3/OGG/M4A/WAV.
 */
export async function uploadRouteFile(file: File): Promise<string> {
  const body = new FormData()
  body.append('file', file)
  const { url } = await apiRequest<{ url: string }>('POST', 'routes', '/uploads', { body, auth: true })
  return url
}

/** Переставить точки: сервис сам расставит `order_index` по этому порядку. */
export function reorderWaypoints(routeId: string, orderedIds: string[]): Promise<Waypoint[]> {
  return apiRequest('POST', 'routes', `/routes/${encodeURIComponent(routeId)}/waypoints/reorder`, {
    body: { ordered_ids: orderedIds },
    auth: true,
  })
}

/**
 * Подсказки на маршруте — интеграции из ТЗ:
 * рядом с точкой есть непроверенная заметка народного архива (п. 6) и у точки
 * нет «живого фото» (п. 7). Обе ручки публичные и считаются отдельно от точек,
 * чтобы не тормозить обычный просмотр маршрута.
 */
export interface ArchivePrompt {
  waypoint_id: string
  entry_id: string
  kind: string
  title: string
  distance_km: number
}

export interface MediaPrompt {
  waypoint_id: string
  poi_id: string
  title: string
}

export function archivePrompts(routeId: string): Promise<ArchivePrompt[]> {
  return apiRequest('GET', 'routes', `/routes/${encodeURIComponent(routeId)}/archive-prompts`)
}

export function mediaPrompts(routeId: string): Promise<MediaPrompt[]> {
  return apiRequest('GET', 'routes', `/routes/${encodeURIComponent(routeId)}/media-prompts`)
}
