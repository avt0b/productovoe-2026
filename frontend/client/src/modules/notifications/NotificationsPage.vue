<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAsync } from '@/core/async'
import { formatDateTime } from '@/core/format'
import { useSessionStore } from '@/core/session'
import { resolveNotificationTarget } from '@/features/notifications/useNotificationWatcher'
import AccountRequired from '@/ui/AccountRequired.vue'
import MsIcon from '@/ui/MsIcon.vue'
import StateBlock from '@/ui/StateBlock.vue'

import { markAllRead, markRead, notificationIcon, listMyNotifications, type AppNotification } from './data'

const session = useSessionStore()
const router = useRouter()

const { data, loading, error, retry } = useAsync<AppNotification[]>(() =>
  session.hasAccount ? listMyNotifications() : Promise.resolve([]),
)

const items = computed(() => data.value ?? [])
const unread = computed(() => items.value.filter((item) => item.read_at === null))

const markingAll = ref(false)
async function readAll(): Promise<void> {
  if (markingAll.value || !unread.value.length) return
  markingAll.value = true
  try {
    await markAllRead(unread.value)
    await retry()
  } finally {
    markingAll.value = false
  }
}

/** Открыли уведомление: отмечаем прочитанным и, если знаем куда, ведём на экран события. */
async function open(item: AppNotification): Promise<void> {
  if (item.read_at === null) {
    void markRead(item.id).catch(() => undefined)
    // data — shallowRef: правим не поле объекта (это не перерисуется), а
    // подменяем сам массив новой копией строки.
    const readAt = new Date().toISOString()
    data.value = items.value.map((row) => (row.id === item.id ? { ...row, read_at: readAt } : row))
  }
  const to = resolveNotificationTarget(item)
  if (to) void router.push(to)
}
</script>

<template>
  <div class="flex w-full flex-col gap-space-md px-margin pb-safe pt-space-md">
    <div v-if="session.hasAccount && !loading && !error" class="flex items-center justify-between gap-space-sm">
      <p class="font-body-sm text-body-sm text-on-surface-variant">
        {{ unread.length ? `Непрочитанных: ${unread.length}` : 'Всё прочитано' }}
      </p>
      <button
        v-if="unread.length"
        type="button"
        class="inline-flex items-center gap-1.5 rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface transition-colors active:scale-95 disabled:opacity-60"
        :disabled="markingAll"
        @click="readAll"
      >
        <MsIcon :name="markingAll ? 'progress_activity' : 'done'" :size="18" :class="{ 'animate-spin': markingAll }" />
        Прочитать всё
      </button>
    </div>

    <AccountRequired v-if="!session.hasAccount" text="Лента уведомлений хранится в аккаунте" />

    <template v-else>
      <StateBlock
        :loading="loading"
        :error="error"
        :empty="!loading && !error && !items.length"
        empty-icon="notifications"
        empty-text="Уведомлений пока нет"
        @retry="retry"
      >
        <ul class="flex flex-col gap-space-sm">
          <li
            v-for="item in items"
            :key="item.id"
            class="rounded-2xl shadow-document"
            :class="item.read_at === null ? 'bg-secondary-container/40' : 'bg-surface-container-lowest'"
          >
            <button type="button" class="flex w-full items-start gap-space-sm p-space-md text-left" @click="open(item)">
              <span
                class="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container"
                aria-hidden="true"
              >
                <MsIcon :name="notificationIcon(item.kind)" :size="20" />
                <span v-if="item.read_at === null" class="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full bg-primary" />
              </span>
              <div class="min-w-0 flex-1">
                <p class="font-label-lg text-label-lg text-on-surface">{{ item.title }}</p>
                <p class="font-body-sm text-body-sm text-on-surface-variant">{{ item.body }}</p>
                <p class="mt-1 font-label-sm text-label-sm text-on-surface-variant">{{ formatDateTime(item.created_at) }}</p>
              </div>
            </button>
          </li>
        </ul>
      </StateBlock>
    </template>
  </div>
</template>
