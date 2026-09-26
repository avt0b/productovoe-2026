import { computed, onBeforeUnmount, ref, shallowRef } from 'vue'
import { useRouter } from 'vue-router'

import { ServiceUnavailableError } from '@/core/api'
import { errorText } from '@/core/format'
import { useGeolocation } from '@/core/geo'
import {
  cancelAlert,
  fetchAlert,
  reportMyPosition,
  resolveAlert,
  respondAlert,
  type LostAlert,
} from '@/features/lost-alert'
import { usePointRoute } from '@/features/point-route'

/** Пока открыт экран — опрос тревоги и отправка своей точки раз в 3 с (CONTRACT 4). */
const POLL_MS = 3000

/**
 * Вся логика экрана поиска: загрузка и опрос тревоги, своя геопозиция и её
 * отправка, маршрут к движущейся цели, действия. Страница только рисует.
 */
export function useLostAlert(alertId: string) {
  const router = useRouter()
  const geo = useGeolocation()
  const pointRoute = usePointRoute({ position: geo.position, status: geo.status, start: geo.start })

  const alert = shallowRef<LostAlert | null>(null)
  const loading = ref(true)
  /** Ошибка только первой загрузки (403/404): дальше сбои опроса не роняют экран. */
  const loadError = ref<string | null>(null)
  const offline = ref(false)
  const busy = ref(false)
  const actionError = ref<string | null>(null)
  /** Тикает раз в секунду — для «последняя точка N с назад». */
  const now = ref(Date.now())

  let poll: ReturnType<typeof setInterval> | undefined
  let clock: ReturnType<typeof setInterval> | undefined
  let lastSentAt = 0

  function apply(next: LostAlert): void {
    alert.value = next
    offline.value = false
  }

  async function first(): Promise<void> {
    loading.value = true
    loadError.value = null
    try {
      apply(await fetchAlert(alertId))
    } catch (reason) {
      loadError.value = errorText(reason)
    } finally {
      loading.value = false
    }
  }

  async function tick(): Promise<void> {
    try {
      apply(await fetchAlert(alertId))
    } catch (reason) {
      // Сеть моргнула — оставляем последнее состояние; ошибку сервиса не прячем в лог.
      if (reason instanceof ServiceUnavailableError) offline.value = true
    }
    void sendPosition()
    void followTarget()
  }

  /** Своя точка на сервер, пока поиск активен. `409` (прогулка закрылась) — молча. */
  async function sendPosition(): Promise<void> {
    const current = alert.value
    const me = geo.position.value
    if (!current || current.status !== 'active' || !me) return
    if (Date.now() - lastSentAt < POLL_MS - 200) return
    lastSentAt = Date.now()
    try {
      await reportMyPosition(current.excursion_id, { lat: me.lat, lon: me.lon, accuracy_m: me.accuracyMeters })
    } catch {
      /* 409 после конца прогулки — не наша забота */
    }
  }

  /** Обновить цель маршрута вслед за тем, к кому идём (он тоже движется). */
  async function followTarget(): Promise<void> {
    const to = routeGoal.value
    if (pointRoute.target.value && to) pointRoute.moveTarget({ id: to.id, lat: to.lat, lon: to.lon })
  }

  // --- кто я и к кому идём ---
  const role = computed(() => alert.value?.my_role ?? 'observer')
  const active = computed(() => alert.value?.status === 'active')

  const meWatcher = computed(() => alert.value?.watchers.find((w) => w.is_me) ?? null)
  const responders = computed(() => (alert.value?.watchers ?? []).filter((w) => w.responding && w.position))
  const nearestResponder = computed(() => responders.value[0] ?? null)

  /** Куда ведёт маршрут: ищущий идёт к потерявшемуся, потерявшийся — к ближайшему ищущему. */
  const routeGoal = computed<{ id: string; lat: number; lon: number } | null>(() => {
    const current = alert.value
    if (!current || current.status !== 'active') return null
    if (role.value === 'watcher') {
      const lost = current.lost.position
      return lost ? { id: `lost-${current.lost.user_id}`, lat: lost.lat, lon: lost.lon } : null
    }
    if (role.value === 'lost') {
      const target = nearestResponder.value ?? current.watchers.find((w) => w.relation === 'guide' && w.position)
      return target?.position ? { id: `watcher-${target.user_id}`, lat: target.position.lat, lon: target.position.lon } : null
    }
    return null
  })

  function startRoute(): void {
    const goal = routeGoal.value
    if (goal) pointRoute.start(goal)
  }

  // --- действия ---
  async function run(action: () => Promise<LostAlert>): Promise<void> {
    if (busy.value) return
    busy.value = true
    actionError.value = null
    try {
      apply(await action())
    } catch (reason) {
      actionError.value = errorText(reason)
    } finally {
      busy.value = false
    }
  }

  async function respondAndGo(): Promise<void> {
    await run(() => respondAlert(alertId))
    if (!actionError.value) startRoute()
  }
  const resolve = () => run(() => resolveAlert(alertId))
  const cancel = () => run(() => cancelAlert(alertId))

  function back(): void {
    if (window.history.length > 1) return void router.back()
    const excursionId = alert.value?.excursion_id
    if (excursionId && router.hasRoute('excursion-walk')) void router.push({ name: 'excursion-walk', params: { excursionId } })
    else if (router.hasRoute('excursions')) void router.push({ name: 'excursions' })
  }

  async function begin(): Promise<void> {
    geo.start()
    await first()
    // Перезапуск приложения уже откликнувшимся ищущим — маршрут включается сам.
    if (active.value && ((role.value === 'watcher' && meWatcher.value?.responding) || role.value === 'lost')) {
      // Потерявшийся в обычном режиме и откликнувшийся ищущий ведутся автоматически;
      // семейный режим для потерявшегося решает страница (кнопкой).
      if (role.value === 'watcher') startRoute()
    }
    poll = setInterval(() => void tick(), POLL_MS)
    clock = setInterval(() => (now.value = Date.now()), 1000)
  }
  void begin()

  onBeforeUnmount(() => {
    clearInterval(poll)
    clearInterval(clock)
    pointRoute.stop()
    geo.stop()
  })

  return {
    alert,
    loading,
    loadError,
    offline,
    busy,
    actionError,
    now,
    role,
    active,
    meWatcher,
    responders,
    nearestResponder,
    routeGoal,
    pointRoute,
    geo,
    respondAndGo,
    resolve,
    cancel,
    startRoute,
    back,
  }
}

export type LostAlertController = ReturnType<typeof useLostAlert>

