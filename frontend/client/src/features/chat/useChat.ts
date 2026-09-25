import { onBeforeUnmount, onMounted, ref } from 'vue'

import { ApiError } from '@/core/api'
import { errorText } from '@/core/format'

import { listMessages, postMessage, streamMessages, type ChatMessage, type ChatSubject } from './api'

/** Паузы перед переподключением потока, мс: сеть на телефоне моргает часто, но сервис дёргать без конца незачем. */
const RETRY_MS = [1000, 3000, 6000, 15_000] as const

function time(message: ChatMessage): number {
  return new Date(message.created_at).getTime()
}

/**
 * Переписка с живым потоком. Сообщения приходят сразу, как их отправили; поток
 * оборвался (сеть, сервис перезапустили, телефон уснул) — переподключаемся и
 * догружаем пропущенное запросом со `since`. Повторы отсекаются по id.
 */
export function useChat(subject: ChatSubject) {
  const messages = ref<ChatMessage[]>([])
  const loading = ref(true)
  const error = ref<string | null>(null)
  /** Поток открыт: новое сообщение появится само. */
  const live = ref(false)
  const sending = ref(false)

  let controller: AbortController | null = null
  let retryTimer: ReturnType<typeof setTimeout> | undefined
  let attempt = 0
  let stopped = false

  function merge(rows: ChatMessage[]): void {
    const known = new Set(messages.value.map((message) => message.id))
    const fresh = rows.filter((row) => !known.has(row.id))
    if (fresh.length) messages.value = [...messages.value, ...fresh].sort((a, b) => time(a) - time(b))
  }

  async function catchUp(): Promise<void> {
    const since = messages.value.at(-1)?.created_at
    merge(await listMessages(subject, since ? { since } : {}))
  }

  async function connect(): Promise<void> {
    if (stopped) return
    clearTimeout(retryTimer)
    controller?.abort()
    const current = new AbortController()
    controller = current
    try {
      await streamMessages(
        subject,
        {
          onReady: () => {
            live.value = true
            attempt = 0
            void catchUp().catch(() => undefined)
          },
          onMessage: (message) => merge([message]),
        },
        current.signal,
      )
    } catch (reason) {
      if (current.signal.aborted) return
      // Доступ закрыли или выезд удалили — переподключение не поможет.
      if (reason instanceof ApiError && [401, 403, 404].includes(reason.status)) {
        live.value = false
        error.value = errorText(reason)
        return
      }
    }
    if (current.signal.aborted || stopped) return
    live.value = false
    retryTimer = setTimeout(() => void connect(), RETRY_MS[Math.min(attempt++, RETRY_MS.length - 1)])
  }

  /** Вернулись в приложение, а поток лёг, пока телефон спал, — не ждать паузу. */
  function onVisible(): void {
    if (document.visibilityState === 'visible' && !live.value) {
      attempt = 0
      void connect()
    }
  }

  async function send(body: string): Promise<boolean> {
    const text = body.trim()
    if (!text || sending.value) return false
    sending.value = true
    error.value = null
    try {
      merge([await postMessage(subject, text)])
      return true
    } catch (reason) {
      error.value = errorText(reason)
      return false
    } finally {
      sending.value = false
    }
  }

  onMounted(async () => {
    document.addEventListener('visibilitychange', onVisible)
    try {
      merge(await listMessages(subject))
    } catch (reason) {
      error.value = errorText(reason)
    } finally {
      loading.value = false
    }
    void connect()
  })

  onBeforeUnmount(() => {
    stopped = true
    clearTimeout(retryTimer)
    controller?.abort()
    document.removeEventListener('visibilitychange', onVisible)
  })

  return { messages, loading, error, live, sending, send }
}
