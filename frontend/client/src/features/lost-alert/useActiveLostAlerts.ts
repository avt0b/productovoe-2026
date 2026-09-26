import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { useSessionStore } from '@/core/session'

import { fetchActiveAlerts, type LostAlert } from './api'

/** Раз в 10 с (CONTRACT 4): сбор длится долго, а нагрузку на сервис бережём. */
const POLL_MS = 10_000

/** Какие тревоги это устройство уже выдёргивало на экран — чтобы не дёргать повторно. */
const OPENED_KEY = 'marshruty.lost.opened'

function readOpened(): string[] {
  try {
    const raw = localStorage.getItem(OPENED_KEY)
    return raw ? (JSON.parse(raw) as string[]) : []
  } catch {
    return []
  }
}

function writeOpened(ids: string[]): void {
  try {
    localStorage.setItem(OPENED_KEY, JSON.stringify(ids.slice(-50)))
  } catch {
    /* приватный режим — переживём до перезапуска */
  }
}

/**
 * Мои открытые тревоги — одни на всё приложение. Опрашивает их плашка, а
 * читают и другие механики: пока кого-то ищут, обычные уведомления ждут
 * (см. [useLostSearchActive]).
 */
const alerts = ref<LostAlert[]>([])

/**
 * Идёт поиск, где я ищущий или меня ищут. Пока идёт, остальные плашки
 * уведомлений не всплывают: «Сбор начался» поверх тревоги только отвлекает, а
 * главное — закрывает саму красную плашку поиска.
 */
export function useLostSearchActive() {
  return computed(() => alerts.value.some((alert) => alert.status === 'active'))
}

/**
 * Следит за моими открытыми тревогами и сам открывает экран поиска, когда
 * появляется новая, где я ищущий или меня ищут (тревогу за меня подняли).
 * Заводится один раз — в плашке [LostAlertBanner]. Ошибки сети глотаются:
 * тревога — не повод показывать ошибку на чужом экране.
 */
export function useActiveLostAlerts() {
  const session = useSessionStore()
  const router = useRouter()
  let opened = readOpened()
  let timer: ReturnType<typeof setInterval> | undefined

  function shouldAutoOpen(alert: LostAlert): boolean {
    if (alert.status !== 'active' || opened.includes(alert.id)) return false
    return alert.my_role === 'watcher' || (alert.my_role === 'lost' && alert.kind === 'reported')
  }

  async function poll(): Promise<void> {
    if (!session.hasAccount || document.visibilityState !== 'visible') return
    let items: LostAlert[]
    try {
      items = await fetchActiveAlerts()
    } catch {
      return
    }
    alerts.value = items

    const toOpen = items.find(shouldAutoOpen)
    if (!toOpen || !router.hasRoute('lost-alert')) return
    // Уже на экране этой тревоги — не выдёргиваем.
    const current = router.currentRoute.value
    if (current.name === 'lost-alert' && current.params.alertId === toOpen.id) {
      opened = [...opened, toOpen.id]
      writeOpened(opened)
      return
    }
    opened = [...opened, toOpen.id]
    writeOpened(opened)
    navigator.vibrate?.([400, 150, 400, 150, 400])
    void router.push({ name: 'lost-alert', params: { alertId: toOpen.id } })
  }

  function refresh(): void {
    void poll()
  }

  function onVisible(): void {
    if (document.visibilityState === 'visible') void poll()
  }

  onMounted(() => {
    timer = setInterval(() => void poll(), POLL_MS)
    void poll()
    document.addEventListener('visibilitychange', onVisible)
  })
  onBeforeUnmount(() => {
    clearInterval(timer)
    document.removeEventListener('visibilitychange', onVisible)
  })

  // Сменился пользователь — прежние тревоги к нему не относятся, спрашиваем заново.
  watch(
    () => session.user?.id,
    () => {
      alerts.value = []
      opened = readOpened()
      void poll()
    },
  )

  return { alerts: computed(() => alerts.value), refresh }
}
