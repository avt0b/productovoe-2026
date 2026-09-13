import type { LatLon } from './types'

const EARTH_RADIUS_KM = 6371

const toRadians = (degrees: number): number => (degrees * Math.PI) / 180

/** Расстояние по поверхности Земли (гаверсинус) — та же формула, что в `map_service`. */
export function distanceKm(a: LatLon, b: LatLon): number {
  const dLat = toRadians(b.lat - a.lat)
  const dLon = toRadians(b.lon - a.lon)
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(toRadians(a.lat)) * Math.cos(toRadians(b.lat)) * Math.sin(dLon / 2) ** 2
  return 2 * EARTH_RADIUS_KM * Math.asin(Math.sqrt(h))
}

/** Длина ломаной по прямым между точками. Пешком по улицам выйдет длиннее. */
export function pathLengthKm(points: LatLon[]): number {
  let total = 0
  for (let i = 1; i < points.length; i += 1) total += distanceKm(points[i - 1], points[i])
  return total
}

/** «350 м», «2,4 км», «18 км». */
export function formatDistance(km: number): string {
  if (km < 1) return `${Math.max(10, Math.round((km * 1000) / 10) * 10)} м`
  const digits = km < 10 ? 1 : 0
  return `${new Intl.NumberFormat('ru-RU', { maximumFractionDigits: digits }).format(km)} км`
}
