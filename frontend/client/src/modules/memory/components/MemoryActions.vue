<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'

import { shareCurrentPage } from '@/core/share'
import MsIcon from '@/ui/MsIcon.vue'

const props = defineProps<{
  heroName: string
  line: string
  folder: string
  mapHint: string
}>()

const COPIED_MS = 2000

const router = useRouter()
const saved = ref(false)
const copied = ref(false)
let copiedTimer: ReturnType<typeof setTimeout> | undefined

/** Карта мемориала — модуль маршрутов. Нет его — кнопка неактивна. */
const canOpenMap = computed(() => router.hasRoute('routes'))

function openMap(): void {
  if (canOpenMap.value) void router.push({ name: 'routes' })
}

async function share(): Promise<void> {
  const result = await shareCurrentPage(`Оживший портрет: ${props.heroName}`, props.line)
  // Системное окно отправки говорит само за себя; сообщение нужно только при копировании.
  if (result !== 'copied') return
  copied.value = true
  clearTimeout(copiedTimer)
  copiedTimer = setTimeout(() => (copied.value = false), COPIED_MS)
}

onBeforeUnmount(() => clearTimeout(copiedTimer))
</script>

<template>
  <div class="flex flex-col space-y-2.5 pt-1">
    <button
      type="button"
      class="flex w-full items-center justify-between rounded-DEFAULT p-3.5 text-on-surface shadow-sm transition-all active:scale-[0.99]"
      :class="saved ? 'bg-secondary-container/30' : 'bg-surface-container-lowest'"
      :aria-pressed="saved"
      @click="saved = !saved"
    >
      <div class="flex min-w-0 items-center gap-3">
        <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-secondary-container/60 text-secondary">
          <MsIcon :name="saved ? 'bookmark_added' : 'bookmark'" :size="20" :filled="saved" />
        </div>
        <div class="flex min-w-0 flex-col text-left">
          <span class="truncate font-label-lg text-label-lg font-bold">
            {{ saved ? 'Сохранено в архив!' : 'Сохранить в семейный архив' }}
          </span>
          <span class="truncate font-body-sm text-body-sm text-outline">{{ folder }}</span>
        </div>
      </div>
      <MsIcon name="chevron_right" :size="20" class="text-outline" />
    </button>

    <button
      type="button"
      class="flex w-full items-center justify-between rounded-DEFAULT bg-surface-container-lowest p-3.5 text-on-surface shadow-sm transition-all active:scale-[0.99] disabled:opacity-60"
      :disabled="!canOpenMap"
      @click="openMap"
    >
      <div class="flex min-w-0 items-center gap-3">
        <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-tertiary-fixed text-tertiary">
          <MsIcon name="star" :size="20" filled />
        </div>
        <div class="flex min-w-0 flex-col text-left">
          <span class="truncate font-label-lg text-label-lg font-bold">Добавить на карту мемориала</span>
          <span class="truncate font-body-sm text-body-sm text-outline">{{ mapHint }}</span>
        </div>
      </div>
      <MsIcon name="chevron_right" :size="20" class="text-outline" />
    </button>

    <button
      type="button"
      class="mt-1 flex h-14 w-full items-center justify-center gap-2.5 rounded-full bg-primary font-label-lg text-label-lg font-bold text-on-primary shadow-lg shadow-primary/25 transition-all active:scale-[0.98]"
      @click="share"
    >
      <MsIcon :name="copied ? 'check_circle' : 'share'" :size="22" />
      <span>{{ copied ? 'Ссылка скопирована!' : 'Поделиться с родными' }}</span>
    </button>
  </div>
</template>
