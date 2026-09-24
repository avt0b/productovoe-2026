import type { DataSource } from '@/core/api'
import { pathLengthKm, type GeoTone, type LatLon } from '@/core/geo'
import { listPoi, type Poi, type PoiKind } from '@/core/services/map'
import { getRoute, listRoutes, type RouteDetail } from '@/core/services/routes'

/**
 * Данные окна «Маршруты»: места слоя «ВОВ» из `map_service` и семейный
 * маршрут дня из `route_service`.
 *
 * Если сервис не ответил, приходит демо-набор Орловщины из
 * `core/services/demoOrel.ts`, а экран показывает плашку «демо-данные».
 */

export interface RouteFilter {
  id: string
  title: string
  icon: string
  /** Подсвеченная категория, даже когда фильтр не выбран. */
  highlight?: boolean
  /** Цвет иконки у невыбранного фильтра. */
  iconClass?: string
  filledIcon?: boolean
}

/**
 * Как места слоя «ВОВ» выглядят на карте. Легенда из кейса: звезда — бой,
 * щит — окоп (шлема в Material Symbols нет), книга — штаб и музей.
 */
export const PLACE_KINDS: Record<PoiKind, { title: string; icon: string; tone: GeoTone }> = {
  battle: { title: 'Места боёв', icon: 'star', tone: 'primary' },
  monument: { title: 'Памятники', icon: 'military_tech', tone: 'secondary' },
  grave: { title: 'Захоронения', icon: 'local_florist', tone: 'neutral' },
  trench: { title: 'Окопы', icon: 'security', tone: 'tertiary' },
  airfield: { title: 'Аэродромы', icon: 'flight', tone: 'tertiary' },
  hospital: { title: 'Госпитали', icon: 'local_hospital', tone: 'primary' },
  other: { title: 'Музеи и штабы', icon: 'menu_book', tone: 'neutral' },
}

const KIND_ORDER: PoiKind[] = ['battle', 'monument', 'grave', 'trench', 'airfield', 'hospital', 'other']

const ICON_CLASS: Record<GeoTone, string> = {
  primary: 'text-primary',
  secondary: 'text-secondary',
  tertiary: 'text-tertiary',
  neutral: 'text-on-surface-variant',
}

export interface MapPlace extends LatLon {
  id: string
  kind: PoiKind
  title: string
  description: string
  dateText: string
  source: string
  /** Кто добавил точку: автор правит и убирает её сам (`_ensure_can_edit` в map_service). */
  createdBy: string
  /** Год события. `null` — дата неизвестна: такие места в хронологию не попадают. */
  year: number | null
}

/**
 * Хронология из кейса: карта показывает не только «где», но и «когда».
 * Орловщина прошла всю войну — от боёв 1941-го под Мценском до освобождения
 * 5 августа 1943-го и до госпиталей 1945-го, поэтому шкала охватывает все годы.
 */
export const TIMELINE_YEARS = [1941, 1942, 1943, 1944, 1945] as const

export interface RouteStop extends LatLon {
  id: string
  /** Номер точки на маршруте, с единицы. */
  step: number
  title: string
  kidTask: string
  hasAr: boolean
  /** То же место на слое «ВОВ» — его отдельную метку прячем, чтобы не рисовать две на одной точке. */
  poiId: string | null
}

export interface FamilyRoute {
  id: string
  title: string
  description: string
  city: string
  distanceKm: number
  durationMinutes: number
  stops: RouteStop[]
}

export interface RoutesOverview {
  places: MapPlace[]
  /** Фильтры — только по тем видам мест, что есть на карте. */
  filters: RouteFilter[]
  route: FamilyRoute | null
  source: DataSource
}

/** Семейный темп с ребёнком и остановки у каждой точки — для оценки времени маршрута. */
const WALKING_KMH = 4
const MINUTES_PER_STOP = 8

export async function fetchRoutesOverview(): Promise<RoutesOverview> {
  const [places, routes] = await Promise.all([listPoi(), listRoutes({ mode: 'family' })])
  const featured = routes.data[0]
  const detail = featured ? await getRoute(featured.id) : null

  const sources = [places.source, routes.source, detail?.source]
  return {
    places: places.data.map(toPlace),
    filters: buildFilters(places.data),
    route: detail ? toRoute(detail.data) : null,
    source: sources.includes('demo') ? 'demo' : 'live',
  }
}

function toPlace(poi: Poi): MapPlace {
  return {
    id: poi.id,
    kind: poi.kind,
    title: poi.title,
    description: poi.description,
    dateText: poi.date_text,
    source: poi.source,
    createdBy: poi.created_by,
    year: eventYear(poi),
    lat: poi.lat,
    lon: poi.lon,
  }
}

/**
 * Год события. Точную дату сервис отдаёт не всегда: у половины архивных
 * записей есть только словесная («осень 1941 года»), поэтому год выцепляем
 * и из неё. Ни там, ни там года нет — место остаётся вне хронологии.
 */
function eventYear(poi: Poi): number | null {
  const iso = poi.event_date ? Number(poi.event_date.slice(0, 4)) : Number.NaN
  if (Number.isFinite(iso)) return iso
  const found = poi.date_text.match(/\b(194[1-5])\b/)
  return found ? Number(found[1]) : null
}

function buildFilters(pois: Poi[]): RouteFilter[] {
  const present = new Set(pois.map((poi) => poi.kind))
  return KIND_ORDER.filter((kind) => present.has(kind)).map((kind) => ({
    id: kind,
    title: PLACE_KINDS[kind].title,
    icon: PLACE_KINDS[kind].icon,
    iconClass: ICON_CLASS[PLACE_KINDS[kind].tone],
    filledIcon: kind === 'battle',
  }))
}

function toRoute(route: RouteDetail): FamilyRoute {
  const stops: RouteStop[] = [...route.waypoints]
    .sort((a, b) => a.order_index - b.order_index)
    .map((waypoint, index) => ({
      id: waypoint.id,
      step: index + 1,
      title: waypoint.title,
      kidTask: waypoint.kid_task,
      hasAr: Boolean(waypoint.ar_hint),
      poiId: waypoint.poi_id,
      lat: waypoint.lat,
      lon: waypoint.lon,
    }))

  // Длину указывает автор маршрута; не указал — считаем по прямым между точками.
  const distanceKm = route.distance_km > 0 ? route.distance_km : Math.round(pathLengthKm(stops) * 10) / 10
  const minutes = (distanceKm / WALKING_KMH) * 60 + stops.length * MINUTES_PER_STOP

  return {
    id: route.id,
    title: route.title,
    description: route.description,
    city: route.city,
    distanceKm,
    durationMinutes: Math.max(5, Math.round(minutes / 5) * 5),
    stops,
  }
}
