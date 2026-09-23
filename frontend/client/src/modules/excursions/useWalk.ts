import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'

import { errorText } from '@/core/format'
import { distanceKm, fetchFootRoute, useGeolocation, type FootRoute, type LatLon } from '@/core/geo'

import { fetchWalk, reportPosition, toPosition, type Walk } from './data'

/** Как часто спрашивать, где группа, мс: люди идут шагом, метки успевают. */
const POLL_MS = 4000

/** Как часто отправлять свою точку, мс: чаще — батарея, реже — метка отстаёт. */
const REPORT_MS = 5000

/**
 * Когда перестраивать маршрут.
 *
 * Роутер публичный и общий на всё сообщество OSM: дёргать его на каждый фикс
 * GPS нельзя. Перестраиваем, когда человек ушёл от точки, откуда строили,
 * дальше порога, или когда краевед сменил цель, — и не чаще раза в интервал.
 */
const REROUTE_AFTER_METERS = 30
const REROUTE_MIN_INTERVAL_MS = 15_000

/** Ближе этого — «вы на месте»: GPS в городе точнее не бывает. */
export const ARRIVED_METERS = 40

/**
 * Прогулка группы глазами одного телефона.
 *
 * Спрашивает, где группа, отправляет свою точку и строит пешеходный маршрут
 * от себя до цели. Экран только рисует — вся хронология здесь.
 */
export function useWalk(excursionId: string) {
  const walk = shallowRef<Walk | null>(null)
  const loadError = ref<string | null>(null)
  const route = shallowRef<FootRoute | null>(null)

  const geo = useGeolocation()

  let pollTimer: ReturnType<typeof setInterval> | undefined
  let reportTimer: ReturnType<typeof setInterval> | undefined
  let routedFrom: LatLon | null = null
  let routedTo: LatLon | null = null
  let routedAt = 0
  let routing = false

  async function refresh(): Promise<void> {
    try {
      walk.value = await fetchWalk(excursionId)
      loadError.value = null
    } catch (reason) {
      // Первая загрузка не удалась — показать; дальше сеть моргает, экран держим.
      if (!walk.value) loadError.value = errorText(reason)
    }
  }

  async function report(): Promise<void> {
    const position = geo.position.value
    if (!position || walk.value?.status !== 'walking') return
    try {
      await reportPosition(excursionId, toPosition(position))
    } catch {
      // Точка не ушла — уйдёт следующая через пять секунд.
    }
  }

  const destination = computed<LatLon | null>(() => {
    const target = walk.value?.destination
    return target ? { lat: target.lat, lon: target.lon } : null
  })

  const metersLeft = computed<number | null>(() => {
    const me = geo.position.value
    const target = destination.value
    return me && target ? distanceKm(me, target) * 1000 : null
  })

  const arrived = computed(() => metersLeft.value !== null && metersLeft.value <= ARRIVED_METERS)

  async function reroute(force = false): Promise<void> {
    const me = geo.position.value
    const target = destination.value
    if (!me || !target || routing || arrived.value) return

    const targetMoved = !routedTo || distanceKm(routedTo, target) * 1000 > 1
    const walkedAway = !routedFrom || distanceKm(routedFrom, me) * 1000 > REROUTE_AFTER_METERS
    const tooSoon = Date.now() - routedAt < REROUTE_MIN_INTERVAL_MS
    if (!force && !targetMoved && (!walkedAway || tooSoon)) return

    routing = true
    try {
      route.value = await fetchFootRoute(me, target)
      routedFrom = { lat: me.lat, lon: me.lon }
      routedTo = target
      routedAt = Date.now()
    } finally {
      routing = false
    }
  }

  // Пришла точка или сменилась цель — возможно, пора перестроить маршрут.
  watch([geo.position, destination], () => void reroute())

  onMounted(() => {
    geo.start()
    void refresh()
    pollTimer = setInterval(() => void refresh(), POLL_MS)
    reportTimer = setInterval(() => void report(), REPORT_MS)
  })

  onBeforeUnmount(() => {
    clearInterval(pollTimer)
    clearInterval(reportTimer)
  })

  return {
    walk,
    loadError,
    route,
    position: geo.position,
    geoStatus: geo.status,
    metersLeft,
    arrived,
    refresh,
    /** После смены цели — перестроить сразу, не дожидаясь следующего фикса. */
    rerouteNow: () => reroute(true),
    startLocating: geo.start,
  }
}
