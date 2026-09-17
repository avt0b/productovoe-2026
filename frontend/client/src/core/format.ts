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

export function errorText(error: unknown): string {
  if (error instanceof Error && error.message) return error.message
  return 'Непредвиденная ошибка'
}
