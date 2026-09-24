import { apiRequest } from '@/core/api'

/**
 * Чат сбора и выезда — `search_hq_service`.
 *
 * Читать и писать может только участник: краевед и записавшиеся на экскурсию,
 * командир и волонтёры выезда (`_ensure_excursion_member` / `_ensure_trip_member`).
 * Сервис же отсеивает брань — тогда ответ приходит ошибкой с понятным текстом.
 */

export interface ChatMessage {
  id: string
  author_id: string
  body: string
  created_at: string
}

/** О чём чат: сбор экскурсии или выезд отряда. */
export interface ChatSubject {
  kind: 'excursion' | 'trip'
  id: string
  /** Заголовок окна — название экскурсии или выезда. */
  title: string
}

function path(subject: ChatSubject): string {
  const base = subject.kind === 'excursion' ? '/excursions' : '/trips'
  return `${base}/${encodeURIComponent(subject.id)}/messages`
}

export function listMessages(subject: ChatSubject, limit = 100): Promise<ChatMessage[]> {
  return apiRequest('GET', 'hq', path(subject), { query: { limit }, auth: true })
}

export function postMessage(subject: ChatSubject, body: string): Promise<ChatMessage> {
  return apiRequest('POST', 'hq', path(subject), { body: { body }, auth: true })
}
