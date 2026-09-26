import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, type RouteLocationRaw } from 'vue-router'

import { useSessionStore } from '@/core/session'
import { useLostSearchActive } from '@/features/lost-alert'

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

/** Что показать и куда вести. Неизвестные виды не всплывают — только лежат в списке. */
export interface NotificationBannerItem {
  notification: AppNotification
  actionLabel: string
  icon: string
  target: RouteLocationRaw
}

interface Kind {
  actionLabel: string
  icon: string
  /**
   * Сколько уведомление имеет смысл всплывать, мс. Сбор живёт полчаса: звать
   * на него через час — значит отправить к пустому месту. Место гибели рядом
   * ждёт помощи сутками, и узнать о нём вечером — не поздно.
   */
  freshMs: number
  /** Куда вести. null — в уведомлении не хватает данных, чтобы вести. */
  target: (notification: AppNotification) => RouteLocationRaw | null
  /**
   * Всплывать ли плашкой. По умолчанию `true`. `false` — уведомление остаётся
   * в ленте и по нажатию ведёт куда надо, но поверх экрана не всплывает:
   * экран тревоги открывает сама фича, дублировать плашкой незачем.
   */
  banner?: boolean
}

const HOUR_MS = 60 * 60_000
const DAY_MS = 24 * HOUR_MS

function toExcursion(route: string) {
  return (notification: AppNotification): RouteLocationRaw | null => {
    const excursionId = notification.payload?.excursion_id
    return typeof excursionId === 'string' ? { name: route, params: { excursionId } } : null
  }
}

/** Экран тревоги по alert_id из payload. */
function toLostAlert(notification: AppNotification): RouteLocationRaw | null {
  const alertId = notification.payload?.alert_id
  return typeof alertId === 'string' ? { name: 'lost-alert', params: { alertId } } : null
}

/** Виды уведомлений, которые всплывают, — подпись кнопки, значок и экран. */
const KINDS: Record<string, Kind> = {
  excursion_gathering_started: {
    actionLabel: 'К сбору',
    icon: 'groups',
    freshMs: HOUR_MS / 2,
    target: toExcursion('excursion-gathering'),
  },
  // Краевед повёл группу: сразу на карту, где все свои и маршрут.
  excursion_walk_started: {
    actionLabel: 'Открыть карту',
    icon: 'directions_walk',
    freshMs: HOUR_MS / 2,
    target: toExcursion('excursion-walk'),
  },
  // «В N км от вас обнаружено место гибели». Какая именно точка, сервис не
  // сообщает — экран «Последний бой» сам откроет место, которому нужна проверка.
  last_stand_nearby: {
    actionLabel: 'Открыть на карте',
    icon: 'person_search',
    freshMs: 24 * HOUR_MS,
    target: () => ({ name: 'last-stand' }),
  },
  // Выезд отменили — ведём в «Штаб»: там же список выездов отряда, карточка сама найдётся.
  trip_cancelled: {
    actionLabel: 'В штаб',
    icon: 'event_busy',
    freshMs: 24 * HOUR_MS,
    target: () => ({ name: 'hq' }),
  },
  // Значок выдал user_service — показываем его в профиле, там уже есть праздник получения.
  achievement: {
    actionLabel: 'Мои значки',
    icon: 'military_tech',
    freshMs: 24 * HOUR_MS,
    target: () => ({ name: 'profile' }),
  },
  // Тревоги: экран поиска открывает и удерживает сама фича lost-alert
  // (плашка + автооткрытие), поэтому дублировать всплытием незачем — banner:false.
  lost_alert: {
    actionLabel: 'Открыть поиск',
    icon: 'sos',
    freshMs: 2 * HOUR_MS,
    target: toLostAlert,
    banner: false,
  },
  lost_alert_searching: {
    actionLabel: 'Открыть карту',
    icon: 'sos',
    freshMs: 2 * HOUR_MS,
    target: toLostAlert,
    banner: false,
  },
  lost_alert_responding: {
    actionLabel: 'Открыть карту',
    icon: 'directions_run',
    freshMs: 2 * HOUR_MS,
    target: toLostAlert,
    banner: false,
  },
  // Поиск закрыт — это уже можно показать плашкой: «нашлись» или «отбой».
  lost_alert_closed: {
    actionLabel: 'Подробнее',
    icon: 'celebration',
    freshMs: HOUR_MS,
    target: toLostAlert,
  },
  rate_excursion: {
    actionLabel: 'Оценить',
    icon: 'star',
    freshMs: 7 * DAY_MS,
    target: (notification) => {
      const excursionId = notification.payload?.excursion_id
      return typeof excursionId === 'string'
        ? { name: 'excursion', params: { excursionId }, query: { rate: '1' } }
        : null
    },
  },
}

/**
 * Куда вести по нажатию на уведомление — общая логика для всплывающего
 * баннера и ленты в центре уведомлений (`modules/notifications`). Неизвестный
 * вид или уведомление без нужных данных в `payload` — `null`, лента тогда
 * просто не переходит никуда, а остаётся на месте.
 */
export function resolveNotificationTarget(notification: AppNotification): RouteLocationRaw | null {
  return KINDS[notification.kind]?.target(notification) ?? null
}

function toBanner(notification: AppNotification, now: number): NotificationBannerItem | null {
  const kind = KINDS[notification.kind]
  if (!kind || kind.banner === false) return null
  if (now - new Date(notification.created_at).getTime() >= kind.freshMs) return null
  const target = kind.target(notification)
  return target ? { notification, actionLabel: kind.actionLabel, icon: kind.icon, target } : null
}

/**
 * Следит за новыми уведомлениями и отдаёт одно — то, что сейчас стоит показать.
 *
 * Показанное один раз больше не всплывает, даже если человек его не открыл и
 * не закрыл: баннер, который возвращается каждые десять секунд, — это спам.
 */
export function useNotificationWatcher() {
  const session = useSessionStore()
  const route = useRoute()
  const searching = useLostSearchActive()
  const current = ref<NotificationBannerItem | null>(null)
  const shown = new Set<string>()
  let timer: ReturnType<typeof setInterval> | undefined

  /**
   * Пока кого-то ищут, плашки молчат: тревога главнее, а плашка уведомления
   * лежит выше красной плашки поиска и закрывала бы её. На самом экране
   * поиска всё и так видно — там им тем более не место. Спрятанное не
   * считается прочитанным и всплывёт, когда поиск закончится.
   */
  const quiet = computed(() => searching.value || route.name === 'lost-alert')

  async function poll(): Promise<void> {
    if (!session.hasAccount || document.visibilityState !== 'visible' || quiet.value) return
    let items: AppNotification[]
    try {
      items = await fetchNotifications()
    } catch {
      return
    }
    const now = Date.now()
    const next = items
      .filter((item) => item.read_at === null && !shown.has(item.id))
      .map((item) => toBanner(item, now))
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

  return { current: computed(() => (quiet.value ? null : current.value)), settle }
}
