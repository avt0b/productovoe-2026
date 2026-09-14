import type { LatLon } from './types'

function toDms(value: number, positive: string, negative: string): string {
  const hemisphere = value >= 0 ? positive : negative
  const totalSeconds = Math.round(Math.abs(value) * 3600)
  const degrees = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  const pad = (n: number): string => String(n).padStart(2, '0')
  return `${degrees}°${pad(minutes)}′${pad(seconds)}″ ${hemisphere}`
}

/** «52°58′04″ N, 36°04′42″ E» — так координаты пишут в полевых отчётах и на картах поисковиков. */
export function formatCoordinates(point: LatLon): string {
  return `${toDms(point.lat, 'N', 'S')}, ${toDms(point.lon, 'E', 'W')}`
}
