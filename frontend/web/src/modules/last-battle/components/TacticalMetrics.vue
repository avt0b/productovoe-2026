<script setup>
const metrics = [
  { icon: 'explore', bg: 'bg-secondary-fixed', fg: 'text-on-secondary-fixed', label: 'Радиус поиска', value: '14.8 км²' },
  { icon: 'person_search', bg: 'bg-tertiary-fixed', fg: 'text-on-tertiary-fixed', label: 'Отрядов на месте', value: '3 группы' },
  { icon: 'badge', bg: 'bg-primary-fixed', fg: 'text-on-primary-fixed', label: 'Медальонов 2024', value: '7 передано' },
]
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
