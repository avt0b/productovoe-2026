import { computed, ref, shallowRef, watch, type Ref } from 'vue'

import {
  distanceKm,
  fetchRoute,
  geolocationProblem,
  travelModeFor,
  type GeolocationStatus,
  type GeoPath,
  type LatLon,
  type TravelMode,
  type TravelRoute,
  type UserPosition,
} from '@/core/geo'

/** Куда ведём: точка карты с её id — по нему карточка понимает, что маршрут к ней. */
export interface RouteTarget extends LatLon {
  id: string
}

/**
 * - `idle` — маршрута нет;
 * - `locating` — ждём, где человек: разрешение, первый фикс GPS;
 * - `denied` — геолокацию запретили: ждать нечего, нужно разрешить и попробовать снова;
 * - `routing` — место известно, маршрут строится;
 * - `active` — маршрут на карте, человек идёт или едет;
 * - `arrived` — на месте.
 */
export type PointRouteState = 'idle' | 'locating' | 'denied' | 'routing' | 'active' | 'arrived'

/** Откуда брать место человека — тот же `useGeolocation`, что рисует «я» на карте окна. */
export interface GeoSource {
  position: Readonly<Ref<UserPosition | null>>
  status: Readonly<Ref<GeolocationStatus>>
  start: () => void
}

/**
 * Когда перестраивать маршрут. Роутер публичный и общий на всё сообщество
 * OSM: дёргать его на каждый фикс GPS нельзя. Перестраиваем, когда человек
 * ушёл от точки, откуда строили, дальше порога, — и не чаще раза в интервал.
 */
const REROUTE_AFTER_METERS: Record<TravelMode, number> = { foot: 30, car: 200 }
const REROUTE_MIN_INTERVAL_MS = 15_000

/** Ближе этого — «вы на месте»: GPS в городе точнее не бывает. */
const ARRIVED_METERS = 40

/**
 * Маршрут от человека до выбранной точки карты.
 *
 * `start(point)` сам спрашивает геолокацию, ждёт первый фикс и строит путь:
 * рядом — пешком, дальше пяти километров — на машине. Пока человек в пути,
 * маршрут перестраивается от того места, где он сейчас. Окно только рисует
 * `path` на своей карте и показывает карточку.
 */
export function usePointRoute(geo: GeoSource) {
  const target = shallowRef<RouteTarget | null>(null)
  const route = shallowRef<TravelRoute | null>(null)
  const mode = ref<TravelMode>('foot')
  const building = ref(false)
  /** Номер поездки: растёт с каждым новым маршрутом, но не с перестройкой по ходу. */
  const trip = ref(0)

  let routedFrom: LatLon | null = null
  let routedAt = 0

  const metersLeft = computed<number | null>(() => {
    const me = geo.position.value
    const to = target.value
    return me && to ? distanceKm(me, to) * 1000 : null
  })

  const arrived = computed(() => metersLeft.value !== null && metersLeft.value <= ARRIVED_METERS)

  const state = computed<PointRouteState>(() => {
    if (!target.value) return 'idle'
    if (arrived.value) return 'arrived'
    if (route.value) return 'active'
    if (geo.position.value) return 'routing'
    return geo.status.value === 'denied' ? 'denied' : 'locating'
  })

  /** Что мешает начать: запрет геолокации или нет спутников. */
  const problem = computed(() => (target.value && !geo.position.value ? geolocationProblem(geo.status.value) : null))

  async function reroute(force = false): Promise<void> {
    const me = geo.position.value
    const to = target.value
    if (!me || !to || building.value || arrived.value) return

    const walkedAway = !routedFrom || distanceKm(routedFrom, me) * 1000 > REROUTE_AFTER_METERS[mode.value]
    const tooSoon = Date.now() - routedAt < REROUTE_MIN_INTERVAL_MS
    if (!force && route.value && (!walkedAway || tooSoon)) return

    // Режим выбираем один раз на поездку: подъехал ближе пяти километров —
    // это всё ещё поездка, а не прогулка.
    if (!route.value) mode.value = travelModeFor(me, to)
    building.value = true
    try {
      const built = await fetchRoute(me, to, mode.value)
      // Пока строили, выбрали другую точку или закончили — этот маршрут уже не нужен.
      if (target.value !== to) return
      route.value = built
      routedFrom = { lat: me.lat, lon: me.lon }
      routedAt = Date.now()
    } finally {
      building.value = false
    }
    // Цель сменили во время постройки — строим к новой, не дожидаясь следующего фикса GPS.
    if (target.value && target.value !== to) void reroute(true)
  }

  function start(point: RouteTarget): void {
    target.value = { id: point.id, lat: point.lat, lon: point.lon }
    route.value = null
    routedFrom = null
    trip.value += 1
    geo.start()
    void reroute(true)
  }

  function stop(): void {
    target.value = null
    route.value = null
    routedFrom = null
  }

  // Пришла новая точка GPS — возможно, пора перестроить (или впервые построить) маршрут.
  watch(geo.position, () => void reroute())

  /** Линия маршрута для карты окна. Прямая «по оценке» — пунктиром. */
  const path = computed<GeoPath | null>(() =>
    route.value && !arrived.value
      ? { id: 'point-route', points: route.value.points, tone: 'primary', dashed: route.value.estimated }
      : null,
  )

  /** Показать весь маршрут, как только он построен, — один раз на поездку. */
  const focus = computed(() => (route.value && target.value ? { key: trip.value, points: route.value.points } : null))

  return {
    target,
    route,
    mode,
    state,
    problem,
    metersLeft,
    building,
    path,
    focus,
    position: geo.position,
    start,
    stop,
  }
}

export type PointRoute = ReturnType<typeof usePointRoute>
