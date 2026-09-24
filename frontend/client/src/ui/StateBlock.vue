<script setup lang="ts">
import MsIcon from './MsIcon.vue'

/**
 * Три состояния экрана — загрузка, ошибка с повтором, пусто — и содержимое.
 *
 * У каждого экрана они обязаны быть: сейчас данные приходят из заглушек
 * мгновенно, но как только их заменят на сервисы, пустой белый экран на
 * медленном мобильном интернете будет выглядеть как поломка.
 */
defineProps<{
  loading: boolean
  error: string | null
  empty?: boolean
  emptyText?: string
  emptyIcon?: string
}>()

defineEmits<{ retry: [] }>()

/** Карточка-документ на пергаменте: та же, что у карточек экранов. */
const BOX =
  'flex flex-col items-center justify-center gap-space-sm rounded-2xl bg-surface-container-lowest p-space-xl text-center shadow-document'
</script>

<template>
  <div v-if="loading" :class="BOX" role="status">
    <MsIcon name="progress_activity" :size="28" class="animate-spin text-primary" />
    <span class="font-label-md text-label-md text-on-surface-variant">Загружаем…</span>
  </div>

  <div v-else-if="error" :class="BOX" role="alert">
    <div class="flex h-12 w-12 items-center justify-center rounded-full bg-error-container text-on-error-container">
      <MsIcon name="cloud_off" :size="26" />
    </div>
    <p class="font-body-sm text-body-sm text-on-surface-variant">{{ error }}</p>
    <button
      type="button"
      class="inline-flex items-center gap-1.5 rounded-full bg-primary-container px-space-md py-2 font-label-md text-label-md text-white shadow-stamp transition-colors hover:bg-primary active:scale-95"
      @click="$emit('retry')"
    >
      <MsIcon name="refresh" :size="18" />
      Повторить
    </button>
  </div>

  <div v-else-if="empty" :class="BOX">
    <div class="flex h-12 w-12 items-center justify-center rounded-full bg-surface-container text-on-surface-variant">
      <MsIcon :name="emptyIcon ?? 'inbox'" :size="26" />
    </div>
    <p class="font-body-sm text-body-sm text-on-surface-variant">{{ emptyText ?? 'Здесь пока пусто' }}</p>
  </div>

  <slot v-else />
</template>
