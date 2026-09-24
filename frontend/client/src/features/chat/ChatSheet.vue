<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'

import { useSessionStore } from '@/core/session'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'

import type { ChatMessage, ChatSubject } from './api'
import { useChat } from './useChat'

/**
 * Переписка группы: краевед со своими на сборе, командир с волонтёрами на
 * выезде. Сообщения приходят потоком — видно сразу, как их отправили.
 */
const props = defineProps<{ subject: ChatSubject }>()

const emit = defineEmits<{ close: [] }>()

const session = useSessionStore()
const { messages, loading, error, live, sending, send } = useChat(props.subject)

const draft = ref('')
const list = ref<HTMLElement | null>(null)

const hostTitle = computed(() => (props.subject.kind === 'excursion' ? 'Краевед' : 'Командир'))
const canSend = computed(() => draft.value.trim().length > 0 && !sending.value)

const DAY = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long' })
const TIME = new Intl.DateTimeFormat('ru-RU', { hour: '2-digit', minute: '2-digit' })

function dayTitle(date: Date): string {
  const today = new Date()
  const yesterday = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 1)
  if (date.toDateString() === today.toDateString()) return 'Сегодня'
  if (date.toDateString() === yesterday.toDateString()) return 'Вчера'
  return DAY.format(date)
}

interface Row {
  message: ChatMessage
  mine: boolean
  author: string
  time: string
  /** Над сообщением — разделитель дня. */
  day: string | null
  /** Тот же автор, что и строкой выше, — подпись не повторяем. */
  continued: boolean
}

const rows = computed<Row[]>(() => {
  let previous: ChatMessage | null = null
  return messages.value.map((message) => {
    const date = new Date(message.created_at)
    const day = !previous || new Date(previous.created_at).toDateString() !== date.toDateString() ? dayTitle(date) : null
    const mine = message.author_id === session.user?.id
    const row: Row = {
      message,
      mine,
      author: mine ? 'Вы' : message.author_id === props.subject.hostId ? hostTitle.value : 'Участник',
      time: TIME.format(date),
      day,
      continued: !day && previous?.author_id === message.author_id,
    }
    previous = message
    return row
  })
})

/** Держим низ переписки, только если человек и так внизу, — не выдёргиваем его из чтения старого. */
function nearBottom(): boolean {
  const element = list.value
  return !element || element.scrollHeight - element.scrollTop - element.clientHeight < 80
}

async function scrollDown(): Promise<void> {
  await nextTick()
  if (list.value) list.value.scrollTop = list.value.scrollHeight
}

watch(
  () => messages.value.length,
  (_length, before) => {
    if (!before || nearBottom() || messages.value.at(-1)?.author_id === session.user?.id) void scrollDown()
  },
)

async function submit(): Promise<void> {
  if (!canSend.value) return
  if (await send(draft.value)) {
    draft.value = ''
    void scrollDown()
  }
}

/** Enter — отправить, Shift+Enter — новая строка, как в любом мессенджере. */
function onKey(event: KeyboardEvent): void {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault()
    void submit()
  }
}
</script>

<template>
  <SheetDialog :title="subject.kind === 'excursion' ? 'Чат сбора' : 'Чат выезда'" :subtitle="subject.title" @close="emit('close')">
    <div class="flex flex-col gap-space-sm">
      <p class="flex items-center gap-space-xs font-label-sm text-label-sm text-on-surface-variant" role="status">
        <span
          class="h-2 w-2 shrink-0 rounded-full transition-colors duration-200"
          :class="live ? 'bg-secondary' : 'bg-outline-variant'"
          aria-hidden="true"
        />
        {{ live ? 'Сообщения приходят сразу' : loading ? 'Подключаемся…' : 'Нет связи — переподключаемся' }}
      </p>

      <div
        ref="list"
        class="flex h-[min(52vh,26rem)] flex-col overflow-y-auto overscroll-contain rounded-2xl bg-surface-container-low p-space-sm"
      >
        <div
          v-if="loading"
          class="m-auto flex items-center gap-space-xs font-label-md text-label-md text-on-surface-variant"
        >
          <MsIcon name="progress_activity" :size="20" class="animate-spin" />
          Загружаем переписку…
        </div>

        <div v-else-if="!rows.length" class="m-auto flex max-w-[28ch] flex-col items-center gap-space-xs text-center">
          <span class="flex h-12 w-12 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container">
            <MsIcon name="forum" :size="24" />
          </span>
          <p class="font-body-sm text-body-sm text-on-surface-variant">
            Сообщений пока нет. Напишите первым: где встречаемся, что взять, кто во сколько будет.
          </p>
        </div>

        <ul v-else class="mt-auto flex flex-col">
          <li v-for="row in rows" :key="row.message.id" class="flex flex-col" :class="row.continued ? 'mt-0.5' : 'mt-space-xs'">
            <p v-if="row.day" class="my-space-xs self-center rounded-full bg-surface-container-high px-space-sm py-0.5 font-label-sm text-label-sm text-on-surface-variant">
              {{ row.day }}
            </p>
            <div class="flex" :class="row.mine ? 'justify-end' : 'justify-start'">
              <div
                class="flex max-w-[85%] flex-col gap-0.5 px-space-sm py-1.5 shadow-document"
                :class="[
                  row.mine
                    ? 'rounded-2xl rounded-br-md bg-secondary-container text-on-secondary-container'
                    : 'rounded-2xl rounded-bl-md bg-surface-container-lowest text-on-surface',
                ]"
              >
                <span
                  v-if="!row.continued && !row.mine"
                  class="font-label-sm text-label-sm"
                  :class="row.author === 'Участник' ? 'text-on-surface-variant' : 'text-secondary'"
                >
                  {{ row.author }}
                </span>
                <span class="whitespace-pre-line break-words font-body-md text-body-md">{{ row.message.body }}</span>
                <span class="self-end font-label-sm text-label-sm opacity-60">{{ row.time }}</span>
              </div>
            </div>
          </li>
        </ul>
      </div>

      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>
    </div>

    <template #footer>
      <form class="flex items-end gap-space-sm" @submit.prevent="submit">
        <label
          class="flex min-w-0 flex-1 items-end rounded-2xl border border-outline-variant bg-surface-container-low px-space-sm py-2 transition-colors duration-200 focus-within:border-secondary focus-within:bg-surface-container-lowest"
        >
          <span class="sr-only">Сообщение группе</span>
          <!-- Поле растёт по тексту до пяти строк (`field-sizing`), дальше прокручивается. -->
          <textarea
            v-model="draft"
            rows="1"
            maxlength="2000"
            placeholder="Сообщение группе"
            class="max-h-[7.5rem] min-w-0 flex-1 resize-none bg-transparent font-body-md text-body-md text-on-surface outline-none [field-sizing:content] placeholder:text-outline"
            @keydown="onKey"
          />
        </label>
        <button
          type="submit"
          aria-label="Отправить"
          class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-secondary text-on-secondary shadow-document transition-all duration-200 active:scale-95 disabled:bg-surface-container-high disabled:text-outline"
          :disabled="!canSend"
        >
          <MsIcon :name="sending ? 'progress_activity' : 'send'" :size="20" :class="{ 'animate-spin': sending }" />
        </button>
      </form>
    </template>
  </SheetDialog>
</template>
