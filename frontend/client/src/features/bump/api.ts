import { apiRequest } from '@/core/api'
import type { UserPosition } from '@/core/geo'

/**
 * Встряска на сервере — `search_hq_service` (`POST /excursions/{id}/bumps`).
 *
 * Сервер ищет встряску второй стороны в том же месте и в то же время: краевед
 * встречает участника, участник — краеведа. Время встряски сервер считает сам:
 * телефон сообщает только, сколько миллисекунд назад тряхнули, — часы телефонов
 * расходятся. Ответ приходит, когда пара нашлась, или через ~2 с.
 */

export type BumpOutcome = 'matched' | 'no_pair' | 'already_checked_in'

export interface BumpResult {
  result: BumpOutcome
  matched_user_ids: string[]
  checked_in_at: string | null
  checked_in_count: number
}

export function sendBump(excursionId: string, position: UserPosition, shakenMsAgo: number): Promise<BumpResult> {
  return apiRequest('POST', 'hq', `/excursions/${encodeURIComponent(excursionId)}/bumps`, {
    body: {
      lat: position.lat,
      lon: position.lon,
      accuracy_m: Math.round(position.accuracyMeters),
      shaken_ms_ago: shakenMsAgo,
    },
    auth: true,
  })
}
