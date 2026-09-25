import { distanceKm } from './distance'
import type { LatLon } from './types'

/**
 * Пешеходный маршрут от человека до места.
 *
 * Своего движка маршрутов у платформы нет, поэтому линию строит публичный
 * OSRM сообщества OpenStreetMap с пешеходным профилем
 * (routing.openstreetmap.de): без ключа, отдаёт CORS, умеет ходить по
 * тротуарам и паркам, а не по проезжей части. Сервис не ответил — рисуем
 * прямую с честной пометкой: направление всё равно полезнее пустой карты.
 */

export interface FootRoute {
  points: LatLon[]
  distanceMeters: number
  durationSeconds: number
  /** Маршрут не построен, это прямая: роутер не ответил. */
  estimated: boolean
}

const ROUTER = 'https://routing.openstreetmap.de/routed-foot/route/v1/foot'

/** Скорость пешком для оценки по прямой, м/с: ~4,5 км/ч, с остановками у светофоров. */
const WALK_SPEED_MPS = 1.25

/** Сколько ждать роутер, мс: в поле сеть медленная, но висеть вечно нельзя. */
const ROUTER_TIMEOUT_MS = 8000

interface OsrmResponse {
  code: string
  routes?: { distance: number; duration: number; geometry: { coordinates: [number, number][] } }[]
}

export async function fetchFootRoute(from: LatLon, to: LatLon): Promise<FootRoute> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), ROUTER_TIMEOUT_MS)
  try {
    // OSRM ждёт долготу первой — наоборот, чем во всём остальном проекте.
    const url = `${ROUTER}/${from.lon},${from.lat};${to.lon},${to.lat}?overview=full&geometries=geojson`
    const response = await fetch(url, { signal: controller.signal })
    if (!response.ok) throw new Error(`OSRM ${response.status}`)
    const body = (await response.json()) as OsrmResponse
    const route = body.routes?.[0]
    if (body.code !== 'Ok' || !route) throw new Error(`OSRM ${body.code}`)
    return {
      points: route.geometry.coordinates.map(([lon, lat]) => ({ lat, lon })),
      distanceMeters: route.distance,
      durationSeconds: route.duration,
      estimated: false,
    }
  } catch {
    return straightLine(from, to)
  } finally {
    clearTimeout(timer)
  }
}

export function straightLine(from: LatLon, to: LatLon): FootRoute {
  const distanceMeters = distanceKm(from, to) * 1000
  return {
    points: [from, to],
    distanceMeters,
    durationSeconds: distanceMeters / WALK_SPEED_MPS,
    estimated: true,
  }
}

/** «12 мин», «1 ч 05 мин» — сколько идти. */
export function formatWalkDuration(seconds: number): string {
  const minutes = Math.max(1, Math.round(seconds / 60))
  if (minutes < 60) return `${minutes} мин`
  const hours = Math.floor(minutes / 60)
  return `${hours} ч ${String(minutes % 60).padStart(2, '0')} мин`
}

/**
 * Пешеходный маршрут во внешнем навигаторе — Яндекс.Картах.
 *
 * Ссылка https, а не `yandexmaps://`: с установленным приложением телефон
 * откроет его, без приложения — сайт. Откуда идём не знаем — Карты спросят
 * сами. `rtt=pd` — пешком.
 */
export function walkingDirectionsUrl(from: LatLon | null, to: LatLon): string {
  const start = from ? `${from.lat},${from.lon}` : ''
  return `https://yandex.ru/maps/?rtext=${start}~${to.lat},${to.lon}&rtt=pd`
}
