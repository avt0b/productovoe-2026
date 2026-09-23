import type { DataSource } from '@/core/api'
import { distanceKm, type LatLon } from '@/core/geo'
import { listPoi } from '@/core/services/map'
import { getRoute } from '@/core/services/routes'

/**
 * Данные окна «Точка маршрута» — точка из `route_service` (`/routes/{id}`).
 *
 * Сервис отдаёт точки только в составе маршрута, поэтому в адресе рядом с
 * точкой идёт маршрут: `/routes/<точка>?route=<маршрут>`. Если сервис не
 * ответил, приходит демо-маршрут Орловщины с теми же id.
 *
 * Архивных кадров «тогда и сейчас» и аудио в сервисе пока нет — эти блоки
 * появятся, когда их начнёт отдавать `media_service`.
 */

export interface RoutePoint {
  id: string
  step: number
  totalSteps: number
  routeTitle: string
  title: string
  place: string
  verifiedBy?: string
  comparison?: {
    archiveImage: string
    archiveLabel: string
    modernImage: string
    modernLabel: string
    source: string
  }
  audio?: {
    title: string
    author: string
    durationSeconds: number
    positionSeconds: number
  }
  quest?: {
    points: number
    title: string
    description: string
    /** Фрагменты, по которым ответ засчитывается. Пусто — задание без ответа, отмечается выполненным. */
    acceptedAnswers: string[]
    success: string
    hint: string
  }
  story?: string
  /** Следующая точка маршрута и расстояние до неё по прямой. У последней точки — `null`. */
  next: { id: string; title: string; distanceKm: number } | null
  /** Подсказка для AR-поиска. Нет — AR на этой точке не предлагаем (например, у братской могилы). */
  arHint: string | null
  /** Где точка на земле — AR наводит на неё. */
  location: LatLon
  /** Аудио рассказа, если автор точки его записал. */
  audioUrl: string | null
  /**
   * Место траурное — братская могила или мемориал. Проводника-маскота там не
   * показываем: у могилы он читается как неуважение. Не знаем, что за место, —
   * считаем траурным.
   */
  solemn: boolean
  source: DataSource
}

/** Очки за семейное задание — одинаковые, пока сервис не научится отдавать свои. */
const QUEST_POINTS = 50

export class PointNotFoundError extends Error {
  constructor() {
    super('Точка маршрута не найдена — возможно, ссылка устарела')
    this.name = 'PointNotFoundError'
  }
}

export async function fetchRoutePoint(pointId: string, routeId: string | null): Promise<RoutePoint> {
  if (!routeId) throw new PointNotFoundError()

  const { data: route, source } = await getRoute(routeId)
  const stops = [...route.waypoints].sort((a, b) => a.order_index - b.order_index)
  const index = stops.findIndex((stop) => stop.id === pointId)
  if (index === -1) throw new PointNotFoundError()

  const stop = stops[index]
  const next = stops[index + 1]

  return {
    id: stop.id,
    step: index + 1,
    totalSteps: stops.length,
    routeTitle: route.title,
    title: stop.title,
    place: [route.city, route.mode === 'family' ? 'семейный маршрут' : 'маршрут'].filter(Boolean).join(' • '),
    quest: stop.kid_task
      ? {
          points: QUEST_POINTS,
          title: 'Задание для юного исследователя',
          description: stop.kid_task,
          acceptedAnswers: [],
          success: 'Задание выполнено — так держать, следопыт!',
          hint: '',
        }
      : undefined,
    story: stop.story || undefined,
    next: next ? { id: next.id, title: next.title, distanceKm: distanceKm(stop, next) } : null,
    arHint: stop.ar_hint || null,
    location: { lat: stop.lat, lon: stop.lon },
    audioUrl: stop.audio_url,
    solemn: await isSolemn(stop.poi_id),
    source,
  }
}

/** Типы мест слоя «ВОВ», где маскоту не место. */
const SOLEMN_KINDS = new Set(['grave', 'monument'])

async function isSolemn(poiId: string | null): Promise<boolean> {
  if (!poiId) return false
  try {
    const { data } = await listPoi()
    const poi = data.find((item) => item.id === poiId)
    // Место неизвестно — считаем траурным: лучше не показать проводника, чем показать его у могилы.
    return poi === undefined || SOLEMN_KINDS.has(poi.kind)
  } catch {
    return true
  }
}
