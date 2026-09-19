/** Мелкие форматтеры, общие для всех окон. */

const DASH = '—'

export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return DASH
  return new Intl.NumberFormat('ru-RU').format(value)
}

export function formatMoney(value: number | null | undefined): string {
  if (value === null || value === undefined) return DASH
  return `${formatNumber(value)} ₽`
}

/**
 * Русское множественное число: `plural(142, ['человек', 'человека', 'человек'])`.
 *
 * Формы — для 1, для 2–4 и для 5–20. Числа 11–14 всегда берут третью форму:
 * «11 дней», а не «11 день».
 */
export function plural(count: number, forms: readonly [string, string, string]): string {
  const n = Math.abs(count) % 100
  const last = n % 10
  if (n > 10 && n < 20) return forms[2]
  if (last === 1) return forms[0]
  if (last >= 2 && last <= 4) return forms[1]
  return forms[2]
}

const DATE = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })
const DATE_TIME = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })

/**
 * «14 сентября 2026». Дата без времени из сервиса (`2026-09-14`) — это день,
 * а не полночь по UTC: иначе к западу от Гринвича она уехала бы на день назад.
 */
export function formatDate(value: string | null | undefined): string {
  if (!value) return DASH
  const date = /^\d{4}-\d{2}-\d{2}$/.test(value) ? new Date(`${value}T00:00:00`) : new Date(value)
  return Number.isNaN(date.getTime()) ? DASH : DATE.format(date)
}

/** «14 сентября, 09:00». */
export function formatDateTime(value: string | null | undefined): string {
  if (!value) return DASH
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? DASH : DATE_TIME.format(date)
}

export function errorText(error: unknown): string {
  if (error instanceof Error && error.message) return error.message
  return 'Непредвиденная ошибка'
}
