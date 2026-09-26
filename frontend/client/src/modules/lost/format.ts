/** «3 с назад», «5 мин назад» — для строки о последней точке потерявшегося. */
export function timeAgo(iso: string, nowMs: number): string {
  const seconds = Math.max(0, Math.round((nowMs - new Date(iso).getTime()) / 1000))
  if (seconds < 60) return `${seconds} с назад`
  return `${Math.round(seconds / 60)} мин назад`
}
