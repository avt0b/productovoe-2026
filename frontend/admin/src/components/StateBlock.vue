<script setup lang="ts">
/**
 * Три обязательных состояния любого экрана: загрузка, ошибка, пусто.
 * Контент показывается только когда все три не сработали.
 */
withDefaults(
  defineProps<{
    loading: boolean
    error?: string | null
    empty?: boolean
    emptyText?: string
    emptyIcon?: string
  }>(),
  { error: null, empty: false, emptyText: 'Ничего не найдено', emptyIcon: 'inbox' },
)

defineEmits<{ retry: [] }>()
</script>

<template>
  <div v-if="loading" class="flex flex-col gap-space-3 py-space-8" role="status" aria-busy="true">
    <div v-for="n in 3" :key="n" class="h-12 animate-pulse rounded-lg bg-surface-container" />
    <span class="sr-only">Загрузка</span>
  </div>

  <div
    v-else-if="error"
    class="flex flex-col items-center gap-space-3 rounded-xl bg-error-container/40 py-space-10 text-center"
  >
    <span class="ms-icon text-[32px] text-error">error</span>
    <p class="font-body-md text-body-md text-on-error-container">{{ error }}</p>
    <button class="btn-secondary btn-sm" type="button" @click="$emit('retry')">
      <span class="ms-icon text-[16px]">refresh</span>
      Повторить
    </button>
  </div>

  <div
    v-else-if="empty"
    class="flex flex-col items-center gap-space-2 py-space-10 text-center text-on-surface-variant"
  >
    <span class="ms-icon text-[32px] text-outline-variant">{{ emptyIcon }}</span>
    <p class="font-body-md text-body-md">{{ emptyText }}</p>
  </div>

  <slot v-else />
</template>
