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
</script>

<template>
  <div
    v-if="loading"
    class="flex flex-col items-center justify-center gap-space-sm rounded-lg bg-surface-container-low p-space-xl text-on-surface-variant"
    role="status"
  >
    <MsIcon name="progress_activity" :size="28" class="animate-spin text-primary" />
    <span class="font-label-md text-label-md">Загружаем…</span>
  </div>

  <div
    v-else-if="error"
    class="flex flex-col items-center justify-center gap-space-sm rounded-lg bg-surface-container-low p-space-xl text-center"
    role="alert"
  >
    <MsIcon name="cloud_off" :size="28" class="text-primary" />
    <p class="font-body-sm text-body-sm text-on-surface-variant">{{ error }}</p>
    <button
      type="button"
      class="rounded-full bg-primary px-space-md py-2 font-label-md text-label-md text-on-primary active:scale-95"
      @click="$emit('retry')"
    >
      Повторить
    </button>
  </div>

  <div
    v-else-if="empty"
    class="flex flex-col items-center justify-center gap-space-sm rounded-lg bg-surface-container-low p-space-xl text-center text-on-surface-variant"
  >
    <MsIcon :name="emptyIcon ?? 'inbox'" :size="28" />
    <p class="font-body-sm text-body-sm">{{ emptyText ?? 'Здесь пока пусто' }}</p>
  </div>

  <slot v-else />
</template>
