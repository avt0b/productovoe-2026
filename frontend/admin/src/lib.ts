/** Мелкие форматтеры, общие для всех экранов. */

const DASH = '—'

export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return DASH
  return new Intl.NumberFormat('ru-RU').format(value)
}

export function formatMoney(value: number | null | undefined): string {
  if (value === null || value === undefined) return DASH
  return `${new Intl.NumberFormat('ru-RU').format(value)} ₽`
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return DASH
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return DASH
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function coords(lat: number, lon: number): string {
  return `${lat.toFixed(5)}, ${lon.toFixed(5)}`
}

/** «Неизвестный боец» вместо пустого места в мемориальных карточках. */
export function soldierName(name: string): string {
  return name.trim() || 'Неизвестный боец'
}

export function errorText(error: unknown): string {
  if (error instanceof Error && error.message) return error.message
  return 'Непредвиденная ошибка'
}
