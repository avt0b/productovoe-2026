import type { ExcursionStatus } from './data'

export const STATUS_LABELS: Record<ExcursionStatus, string> = {
  scheduled: 'Идёт запись',
  gathering: 'Идёт сбор группы',
  walking: 'Группа идёт',
  finished: 'Завершена',
  cancelled: 'Отменена',
}

const startFormat = new Intl.DateTimeFormat('ru-RU', {
  weekday: 'short',
  day: 'numeric',
  month: 'long',
  hour: '2-digit',
  minute: '2-digit',
})

/** «сб, 20 сентября, 14:00» — в часовом поясе телефона. */
export function formatStart(iso: string): string {
  return startFormat.format(new Date(iso))
}

const timeFormat = new Intl.DateTimeFormat('ru-RU', { hour: '2-digit', minute: '2-digit' })

export function formatTime(iso: string): string {
  return timeFormat.format(new Date(iso))
}

/** Сколько целых минут осталось до `iso`; прошло — 0. */
export function minutesLeft(iso: string | null, now: number): number | null {
  if (!iso) return null
  return Math.max(0, Math.ceil((new Date(iso).getTime() - now) / 60_000))
}

/** Имён в сервисе нет — участника показываем по началу id, пока профили не переехали в user_service. */
export function participantLabel(userId: string): string {
  return `Участник #${userId.slice(0, 4)}`
}
