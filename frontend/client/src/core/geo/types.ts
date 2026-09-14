/** Точка на земле. Порядок и имена полей — как в сервисах: `lat`, `lon`. */
export interface LatLon {
  lat: number
  lon: number
}

export interface UserPosition extends LatLon {
  accuracyMeters: number
}

/** Цвет метки — роль палитры, а не hex: карта берёт цвета из тех же токенов, что и вёрстка. */
export type GeoTone = 'primary' | 'secondary' | 'tertiary' | 'neutral'

export interface GeoMarker extends LatLon {
  id: string
  /** Подпись у выбранной метки и всплывающая подсказка. */
  label: string
  /** Имя иконки Material Symbols. */
  icon: string
  tone: GeoTone
  /** Короткий текст вместо иконки — номер точки маршрута. */
  badge?: string
}

export interface GeoPath {
  id: string
  points: LatLon[]
  tone: GeoTone
  /** Пунктир — «след» маршрута. */
  dashed?: boolean
}

/** Центр Орла: сюда смотрит карта, пока меток нет. */
export const OREL_CENTER: LatLon = { lat: 52.9686, lon: 36.0694 }
