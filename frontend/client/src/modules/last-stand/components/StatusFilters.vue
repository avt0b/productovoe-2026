<script setup lang="ts">
import { STATUS_LABELS, type FindStatus } from '../data'

const visible = defineModel<Set<FindStatus>>({ required: true })

defineProps<{
  /** Сколько мест в каждой стадии: фильтр заодно работает сводкой. */
  counts: Record<FindStatus, number>
}>()

/** Цвет стадии — тот же, что у метки на карте: фильтр читается как легенда. */
const TONES: Record<FindStatus, { on: string; dot: string }> = {
  found: { on: 'bg-primary-fixed text-on-primary-fixed-variant', dot: 'bg-primary' },
  confirmed: { on: 'bg-tertiary-fixed text-on-tertiary-fixed', dot: 'bg-tertiary' },
  raised: { on: 'bg-secondary-container text-on-secondary-container', dot: 'bg-secondary' },
}

const ORDER: FindStatus[] = ['found', 'confirmed', 'raised']

function toggle(status: FindStatus): void {
  const next = new Set(visible.value)
  if (next.has(status)) next.delete(status)
  else next.add(status)
  visible.value = next
}
</script>

<template>
  <div class="no-scrollbar -mx-margin flex items-center gap-space-xs overflow-x-auto px-margin pb-1">
    <button
      v-for="status in ORDER"
      :key="status"
      type="button"
      :aria-pressed="visible.has(status)"
      class="flex shrink-0 items-center gap-1.5 rounded-full px-3 py-1.5 font-label-md text-label-md transition-colors duration-200 active:scale-95"
      :class="visible.has(status) ? `${TONES[status].on} shadow-document` : 'bg-surface-container-high text-on-surface-variant'"
      @click="toggle(status)"
    >
      <span class="h-2 w-2 rounded-full" :class="visible.has(status) ? TONES[status].dot : 'bg-outline'" />
      <span>{{ STATUS_LABELS[status] }}</span>
      <span class="font-label-sm text-label-sm opacity-70">{{ counts[status] }}</span>
    </button>
  </div>
</template>
