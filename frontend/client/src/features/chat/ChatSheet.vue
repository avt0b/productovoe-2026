<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

import { errorText, formatDateTime } from '@/core/format'
import { useSessionStore } from '@/core/session'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'

import { listMessages, postMessage, type ChatMessage, type ChatSubject } from './api'

/**
 * Переписка группы: краевед со своими на сборе, командир с волонтёрами на
 * выезде. Пуша на стенде нет, поэтому окно само перечитывает сообщения, пока
 * открыто, — раз в десять секунд, как баннер уведомлений.
 */
const props = defineProps<{ subject: ChatSubject }>()

const emit = defineEmits<{ close: [] }>()

/** Как часто перечитывать переписку, мс. */
const POLL_MS = 10_000

const session = useSessionStore()

const messages = ref<ChatMessage[]>([])
const draft = ref('')
const loading = ref(true)
const sending = ref(false)
const error = ref<string | null>(null)
const list = ref<HTMLElement | null>(null)
let timer: ReturnType<typeof setInterval> | undefined

const canSend = computed(() => draft.value.trim().length > 0 && !sending.value)

function mine(message: ChatMessage): boolean {
  return message.author_id === session.user?.id
}

async function scrollDown(): Promise<void> {
  await nextTick()
  if (list.value) list.value.scrollTop = list.value.scrollHeight
}

async function load(initial = false): Promise<void> {
  try {
    const rows = await listMessages(props.subject)
    const grew = rows.length !== messages.value.length
    messages.value = rows
    error.value = null
    if (initial || grew) void scrollDown()
  } catch (reason) {
    // Молчим при фоновом обновлении: показывать ошибку поверх переписки незачем.
    if (initial) error.value = errorText(reason)
  } finally {
    if (initial) loading.value = false
  }
}

async function send(): Promise<void> {
  if (!canSend.value) return
  sending.value = true
  error.value = null
  try {
    messages.value = [...messages.value, await postMessage(props.subject, draft.value.trim())]
    draft.value = ''
    void scrollDown()
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    sending.value = false
  }
}

onMounted(() => {
  void load(true)
  timer = setInterval(() => void load(), POLL_MS)
})

onBeforeUnmount(() => clearInterval(timer))
</script>

<template>
  <SheetDialog :title="subject.kind === 'excursion' ? 'Чат сбора' : 'Чат выезда'" :subtitle="subject.title" @close="emit('close')">
    <div class="flex flex-col gap-space-sm">
      <div
        v-if="loading"
        class="flex items-center justify-center gap-space-xs py-space-lg font-label-md text-label-md text-on-surface-variant"
        role="status"
      >
        <MsIcon name="progress_activity" :size="20" class="animate-spin" />
        Загружаем переписку…
      </div>

      <p
        v-else-if="!messages.length"
        class="rounded-2xl bg-surface-container-low p-space-md text-center font-body-sm text-body-sm text-on-surface-variant"
      >
        Сообщений пока нет. Напишите первым: где встречаемся, что взять, кто во сколько будет.
      </p>

      <ul v-else ref="list" class="flex max-h-72 flex-col gap-space-xs overflow-y-auto">
        <li v-for="message in messages" :key="message.id" class="flex" :class="mine(message) ? 'justify-end' : 'justify-start'">
          <div
            class="flex max-w-[85%] flex-col gap-0.5 rounded-2xl px-space-sm py-2"
            :class="mine(message) ? 'bg-secondary-container text-on-secondary-container' : 'bg-surface-container-low text-on-surface'"
          >
            <span class="font-archival text-archival uppercase opacity-70">
              {{ mine(message) ? 'Вы' : 'Участник' }} · {{ formatDateTime(message.created_at) }}
            </span>
            <span class="whitespace-pre-line font-body-md text-body-md">{{ message.body }}</span>
          </div>
        </li>
      </ul>

      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>

      <form class="flex items-end gap-space-sm" @submit.prevent="send">
        <textarea
          v-model="draft"
          rows="2"
          maxlength="2000"
          placeholder="Сообщение группе"
          aria-label="Сообщение группе"
          class="min-w-0 flex-1 resize-none rounded-DEFAULT border-b border-outline-variant bg-surface-container-low px-space-sm py-2 font-body-md text-body-md text-on-surface outline-none placeholder:text-outline focus-within:border-primary"
        />
        <button
          type="submit"
          aria-label="Отправить"
          class="mb-0.5 flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-primary-container text-white shadow-stamp active:scale-95 disabled:opacity-60"
          :disabled="!canSend"
        >
          <MsIcon :name="sending ? 'progress_activity' : 'send'" :size="20" :class="{ 'animate-spin': sending }" />
        </button>
      </form>
    </div>
  </SheetDialog>
</template>
