<script setup lang="ts">
import MsIcon from '@/ui/MsIcon.vue'

const query = defineModel<string>({ required: true })
</script>

<template>
  <div
    class="flex w-full items-center justify-between gap-space-sm rounded-full bg-surface-container-lowest px-space-md py-2.5 shadow-sm"
  >
    <label class="flex min-w-0 flex-1 items-center gap-space-sm">
      <MsIcon name="search" :size="22" class="text-outline" />
      <span class="sr-only">Поиск по маршрутам</span>
      <input
        v-model="query"
        type="search"
        placeholder="Поиск памятников, дивизий, сел..."
        class="w-full border-none bg-transparent p-0 font-body-sm text-body-sm text-on-surface outline-none placeholder:text-outline"
      />
    </label>
    <div class="flex shrink-0 items-center gap-space-xs">
      <button
        type="button"
        aria-label="Голосовой поиск"
        class="flex h-8 w-8 items-center justify-center rounded-full bg-surface-container-low text-on-surface-variant transition-colors hover:text-primary"
      >
        <MsIcon name="mic" :size="18" />
      </button>
      <button
        type="button"
        aria-label="Компас"
        class="flex h-8 w-8 items-center justify-center rounded-full bg-primary-fixed text-on-primary-fixed-variant transition-transform hover:scale-105"
      >
        <MsIcon name="explore" :size="18" />
      </button>
    </div>
  </div>
</template>
