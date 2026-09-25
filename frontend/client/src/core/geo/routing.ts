import { distanceKm } from './distance'
import type { LatLon } from './types'

/**
 * Маршрут от человека до места.
 *
 * Своего движка маршрутов у платформы нет, поэтому линию строит публичный
 * OSRM сообщества OpenStreetMap (routing.openstreetmap.de): без ключа, отдаёт
 * CORS. Пешком он ходит по тротуарам и паркам, а не по проезжей части, на
 * машине — по дорогам. Сервис не ответил — рисуем прямую с честной пометкой:
 * направление всё равно полезнее пустой карты.
 */

/** Как добираться: пешком или на машине — места «Последнего боя» обычно в поле за деревней. */
export type TravelMode = 'foot' | 'car'

export interface TravelRoute {
  mode: TravelMode
  points: LatLon[]
  distanceMeters: number
  durationSeconds: number
  /** Маршрут не построен, это прямая: роутер не ответил. */
  estimated: boolean
}

/** Пешеходный маршрут — прогулка группы за краеведом ходит только пешком. */
export type FootRoute = TravelRoute

const ROUTERS: Record<TravelMode, string> = {
  foot: 'https://routing.openstreetmap.de/routed-foot/route/v1/foot',
  car: 'https://routing.openstreetmap.de/routed-car/route/v1/driving',
}

/**
 * Скорость для оценки по прямой, м/с: пешком ~4,5 км/ч с остановками у
 * светофоров, на машине ~40 км/ч — просёлки и деревни, не трасса.
 */
const SPEED_MPS: Record<TravelMode, number> = { foot: 1.25, car: 11 }

/** Дальше этого пешком не предлагаем: пять километров — час ходу, дальше едут. */
export const WALKABLE_KM = 5

/** Сколько ждать роутер, мс: в поле сеть медленная, но висеть вечно нельзя. */
const ROUTER_TIMEOUT_MS = 8000

interface OsrmResponse {
  code: string
  routes?: { distance: number; duration: number; geometry: { coordinates: [number, number][] } }[]
}

/** Пешком — если место рядом, иначе на машине. */
export function travelModeFor(from: LatLon, to: LatLon): TravelMode {
  return distanceKm(from, to) > WALKABLE_KM ? 'car' : 'foot'
}

export async function fetchRoute(from: LatLon, to: LatLon, mode: TravelMode): Promise<TravelRoute> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), ROUTER_TIMEOUT_MS)
  try {
    // OSRM ждёт долготу первой — наоборот, чем во всём остальном проекте.
    const url = `${ROUTERS[mode]}/${from.lon},${from.lat};${to.lon},${to.lat}?overview=full&geometries=geojson`
    const response = await fetch(url, { signal: controller.signal })
    if (!response.ok) throw new Error(`OSRM ${response.status}`)
    const body = (await response.json()) as OsrmResponse
    const route = body.routes?.[0]
    if (body.code !== 'Ok' || !route) throw new Error(`OSRM ${body.code}`)
    return {
      mode,
      points: route.geometry.coordinates.map(([lon, lat]) => ({ lat, lon })),
      distanceMeters: route.distance,
      durationSeconds: route.duration,
      estimated: false,
    }
  } catch {
    return straightLine(from, to, mode)
  } finally {
    clearTimeout(timer)
  }
}

export function fetchFootRoute(from: LatLon, to: LatLon): Promise<FootRoute> {
  return fetchRoute(from, to, 'foot')
}

export function straightLine(from: LatLon, to: LatLon, mode: TravelMode = 'foot'): TravelRoute {
  const distanceMeters = distanceKm(from, to) * 1000
  return {
    mode,
    points: [from, to],
    distanceMeters,
    durationSeconds: distanceMeters / SPEED_MPS[mode],
    estimated: true,
  }
}

/** «12 мин», «1 ч 05 мин» — сколько в пути. */
export function formatWalkDuration(seconds: number): string {
  const minutes = Math.max(1, Math.round(seconds / 60))
  if (minutes < 60) return `${minutes} мин`
  const hours = Math.floor(minutes / 60)
  return `${hours} ч ${String(minutes % 60).padStart(2, '0')} мин`
}

/**
 * Маршрут во внешнем навигаторе — Яндекс.Картах: голосом и с поворотами они
 * ведут лучше нас.
 *
 * Ссылка https, а не `yandexmaps://`: с установленным приложением телефон
 * откроет его, без приложения — сайт. Откуда идём не знаем — Карты спросят
 * сами. `rtt=pd` — пешком, `rtt=auto` — на машине.
 */
export function directionsUrl(from: LatLon | null, to: LatLon, mode: TravelMode): string {
  const start = from ? `${from.lat},${from.lon}` : ''
  return `https://yandex.ru/maps/?rtext=${start}~${to.lat},${to.lon}&rtt=${mode === 'car' ? 'auto' : 'pd'}`
}

export function walkingDirectionsUrl(from: LatLon | null, to: LatLon): string {
  return directionsUrl(from, to, 'foot')
}
