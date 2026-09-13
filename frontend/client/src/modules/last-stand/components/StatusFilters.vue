<script setup lang="ts">
import { STATUS_LABELS, type FindStatus } from '../data'

const visible = defineModel<Set<FindStatus>>({ required: true })

/** Цвет стадии: тот же, что у метки на карте, — чтобы фильтр читался как легенда. */
const TONES: Record<FindStatus, { on: string; dot: string }> = {
  found: { on: 'bg-primary-fixed text-on-primary-fixed-variant', dot: 'bg-primary' },
  confirmed: { on: 'bg-secondary-container text-on-secondary-container', dot: 'bg-secondary' },
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
      class="flex shrink-0 items-center gap-1.5 rounded-full px-3 py-1.5 font-label-md text-label-md transition-transform active:scale-95"
      :class="visible.has(status) ? `${TONES[status].on} shadow-sm` : 'bg-surface-container-high text-on-surface-variant opacity-70'"
      @click="toggle(status)"
    >
      <span class="h-2 w-2 rounded-full" :class="TONES[status].dot" />
      <span>{{ STATUS_LABELS[status] }}</span>
    </button>
  </div>
</template>
