import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { RouteLocationRaw } from 'vue-router'

import { useSessionStore } from '@/core/session'

import { fetchNotifications, markNotificationRead, type AppNotification } from './api'

/**
 * Как часто спрашивать уведомления, мс.
 *
 * Пуша на стенде нет (FCM не настроен), поэтому приложение спрашивает само.
 * Десять секунд: сбор длится полчаса, и узнать о нём через десять секунд —
 * всё равно что сразу; чаще — лишняя нагрузка на user_service от каждого
 * открытого приложения.
 */
const POLL_MS = 10_000

/**
 * Уведомления старше этого не всплывают, мс.
 *
 * Сбор живёт тридцать минут: звать на него человека, открывшего приложение
 * через час, — значит отправить его к пустому месту.
 */
const FRESH_MS = 30 * 60_000

/** Что показать и куда вести. Неизвестные виды не всплывают — только лежат в списке. */
export interface NotificationBannerItem {
  notification: AppNotification
  actionLabel: string
  target: RouteLocationRaw
}

/** Куда ведёт уведомление каждого вида: подпись кнопки и экран. */
const EXCURSION_TARGETS: Record<string, { actionLabel: string; route: string }> = {
  excursion_gathering_started: { actionLabel: 'К сбору', route: 'excursion-gathering' },
  // Краевед повёл группу: сразу на карту, где все свои и маршрут.
  excursion_walk_started: { actionLabel: 'Открыть карту', route: 'excursion-walk' },
}

function toBanner(notification: AppNotification): NotificationBannerItem | null {
  const target = EXCURSION_TARGETS[notification.kind]
  const excursionId = notification.payload?.excursion_id
  if (!target || typeof excursionId !== 'string') return null
  return {
    notification,
    actionLabel: target.actionLabel,
    target: { name: target.route, params: { excursionId } },
  }
}

/**
 * Следит за новыми уведомлениями и отдаёт одно — то, что сейчас стоит показать.
 *
 * Показанное один раз больше не всплывает, даже если человек его не открыл и
 * не закрыл: баннер, который возвращается каждые десять секунд, — это спам.
 */
export function useNotificationWatcher() {
  const session = useSessionStore()
  const current = ref<NotificationBannerItem | null>(null)
  const shown = new Set<string>()
  let timer: ReturnType<typeof setInterval> | undefined

  async function poll(): Promise<void> {
    if (!session.hasAccount || document.visibilityState !== 'visible') return
    let items: AppNotification[]
    try {
      items = await fetchNotifications()
    } catch {
      return
    }
    const now = Date.now()
    const next = items
      .filter((item) => item.read_at === null && !shown.has(item.id))
      .filter((item) => now - new Date(item.created_at).getTime() < FRESH_MS)
      .map(toBanner)
      .find((item): item is NotificationBannerItem => item !== null)
    if (!next || current.value) return
    shown.add(next.notification.id)
    current.value = next
    navigator.vibrate?.([80, 60, 80])
  }

  /** Человек увидел: открыл или закрыл. В обоих случаях — прочитано. */
  function settle(): void {
    const item = current.value
    current.value = null
    if (item) void markNotificationRead(item.notification.id).catch(() => undefined)
  }

  function start(): void {
    clearInterval(timer)
    timer = setInterval(() => void poll(), POLL_MS)
    void poll()
  }

  // Вернулись в приложение — сразу проверить, не ждать до десяти секунд.
  function onVisible(): void {
    if (document.visibilityState === 'visible') void poll()
  }

  onMounted(() => {
    start()
    document.addEventListener('visibilitychange', onVisible)
  })
  onBeforeUnmount(() => {
    clearInterval(timer)
    document.removeEventListener('visibilitychange', onVisible)
  })

  // Вошли под другим человеком — старые «показанные» к нему не относятся.
  watch(
    () => session.user?.id,
    () => {
      shown.clear()
      current.value = null
      void poll()
    },
  )

  return { current: computed(() => current.value), settle }
}
