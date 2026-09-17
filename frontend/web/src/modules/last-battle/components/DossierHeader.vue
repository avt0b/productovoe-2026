<script setup>
import { computed } from 'vue'

const props = defineProps({
  point: { type: Object, default: null },
})

const title = computed(() => props.point?.soldier_name || 'Неизвестный боец')
const dateAndPlace = computed(() => {
  if (!props.point) return ''
  return [props.point.date_text, props.point.unit].filter(Boolean).join(' • ')
})
</script>

<template>
  <div class="flex flex-col gap-2">
    <div class="flex items-center justify-between flex-wrap gap-2">
      <span
        v-if="point"
        class="px-3 py-1 rounded-full bg-tertiary-fixed text-on-tertiary-fixed font-label-sm text-label-sm font-bold tracking-wide uppercase"
      >
        Точка map_service № {{ point.id.slice(0, 8) }}
      </span>
      <span class="flex items-center gap-1.5 font-label-sm text-label-sm text-secondary font-bold">
        <span class="w-2 h-2 rounded-full bg-secondary" />
        Запись обновляется онлайн
      </span>
    </div>
    <h1 class="font-headline-lg text-headline-lg text-on-surface font-extrabold tracking-tight leading-snug">{{ title }}</h1>
    <div v-if="dateAndPlace" class="flex items-center gap-2 text-on-surface-variant font-label-md text-label-md">
      <span class="material-symbols-outlined text-[18px] text-primary">calendar_today</span>
      <span>{{ dateAndPlace }}</span>
    </div>
  </div>
</template>
