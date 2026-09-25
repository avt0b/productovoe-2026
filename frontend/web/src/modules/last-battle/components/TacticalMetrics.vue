<script setup>
import { computed } from 'vue'

const props = defineProps({
  points: { type: Array, default: () => [] },
})

// "Радиус поиска" и "Отрядов на месте" — таких данных на бэкенде нет,
// оставлены как декоративная витрина. "Останков поднято" — честный счётчик
// по реальным точкам (status === remains_raised).
const raisedCount = computed(() => props.points.filter((p) => p.status === 'remains_raised').length)

const metrics = computed(() => [
  { icon: 'explore', bg: 'bg-secondary-fixed', fg: 'text-on-secondary-fixed', label: 'Радиус поиска', value: '14.8 км²' },
  { icon: 'person_search', bg: 'bg-tertiary-fixed', fg: 'text-on-tertiary-fixed', label: 'Отрядов на месте', value: '3 группы' },
  {
    icon: 'badge',
    bg: 'bg-primary-fixed',
    fg: 'text-on-primary-fixed',
    label: 'Останков поднято',
    value: `${raisedCount.value} из ${props.points.length}`,
  },
])
</script>

<template>
  <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
    <div
      v-for="metric in metrics"
      :key="metric.label"
      class="bg-surface-container-lowest p-3.5 rounded-DEFAULT shadow-sm flex items-center gap-3"
    >
      <div class="w-10 h-10 rounded-full flex items-center justify-center shrink-0" :class="[metric.bg, metric.fg]">
        <span class="material-symbols-outlined text-[20px]">{{ metric.icon }}</span>
      </div>
      <div>
        <span class="font-label-sm text-label-sm text-on-surface-variant">{{ metric.label }}</span>
        <div class="font-headline-sm text-headline-sm text-on-surface font-bold">{{ metric.value }}</div>
      </div>
    </div>
  </div>
</template>
