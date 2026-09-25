import { apiRequest, apiStream } from '@/core/api'

/**
 * Чат сбора и выезда — `search_hq_service`.
 *
 * Читать и писать может только участник: краевед и записавшиеся на экскурсию,
 * командир и волонтёры выезда (`_ensure_excursion_member` / `_ensure_trip_member`).
 * Сервис же отсеивает брань — тогда ответ приходит ошибкой с понятным текстом.
 * Новые сообщения приходят потоком (`/messages/stream`), а не опросом.
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
  /** Кто ведёт: командир отряда или краевед — его сообщения подписаны. */
  hostId?: string
}

function path(subject: ChatSubject, rest = ''): string {
  const base = subject.kind === 'excursion' ? '/excursions' : '/trips'
  return `${base}/${encodeURIComponent(subject.id)}/messages${rest}`
}

/** Последние сообщения по порядку. `since` — только написанные не раньше (догрузить пропущенное). */
export function listMessages(subject: ChatSubject, options: { limit?: number; since?: string } = {}): Promise<ChatMessage[]> {
  return apiRequest('GET', 'hq', path(subject), { query: { limit: options.limit ?? 100, since: options.since }, auth: true })
}

export function postMessage(subject: ChatSubject, body: string): Promise<ChatMessage> {
  return apiRequest('POST', 'hq', path(subject), { body: { body }, auth: true })
}

export interface StreamHandlers {
  /** Подписка на сервере уже есть — самое время догрузить пропущенное. */
  onReady(): void
  onMessage(message: ChatMessage): void
}

/**
 * Держать поток новых сообщений, пока не сработает `signal` или сервер не
 * закроет соединение. Разбор Server-Sent Events — минимальный: сервис шлёт
 * только `event:` и однострочный `data:`, комментарии — пустые пинги.
 */
export async function streamMessages(subject: ChatSubject, handlers: StreamHandlers, signal: AbortSignal): Promise<void> {
  const response = await apiStream('hq', path(subject, '/stream'), signal)
  if (!response.body) throw new Error('Поток без тела')
  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader()
  let buffer = ''
  for (;;) {
    const { value, done } = await reader.read()
    if (done) return
    buffer += value.replaceAll('\r\n', '\n')
    let end = buffer.indexOf('\n\n')
    while (end >= 0) {
      dispatch(buffer.slice(0, end), handlers)
      buffer = buffer.slice(end + 2)
      end = buffer.indexOf('\n\n')
    }
  }
}

function dispatch(block: string, handlers: StreamHandlers): void {
  let event = 'message'
  const data: string[] = []
  for (const line of block.split('\n')) {
    if (line.startsWith('event:')) event = line.slice(6).trim()
    else if (line.startsWith('data:')) data.push(line.slice(5).trimStart())
  }
  if (event === 'ready') handlers.onReady()
  else if (event === 'message' && data.length) handlers.onMessage(JSON.parse(data.join('\n')) as ChatMessage)
}
