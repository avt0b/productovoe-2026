<script setup>
// Ни один из этих показателей не хранится ни в одном сервисе — нет ручки,
// которая считала бы пройденные маршруты/проверки/очки конкретного
// пользователя. Демо-заглушка, пока такая статистика не появится на бэке.
const metrics = [
  { icon: 'hiking', value: '7', label: 'Маршрутов пройдено', bg: 'bg-secondary-container', fg: 'text-on-secondary-container' },
  { icon: 'fact_check', value: '3', label: 'Находки проверено в ЦАМО', bg: 'bg-primary-fixed', fg: 'text-on-primary-fixed' },
  { icon: 'stars', value: '1 250', label: 'Очков следопыта', bg: 'bg-tertiary-fixed', fg: 'text-on-tertiary-fixed' },
  { icon: 'flag_circle', value: 'Сезон VI', label: 'Вахта Памяти 2024', bg: 'bg-secondary-fixed', fg: 'text-on-secondary-fixed' },
]
</script>

<template>
  <div class="flex flex-col gap-2 mb-8">
    <span class="self-start px-2.5 py-1 rounded-full bg-surface-container-high text-on-surface-variant font-label-sm text-label-sm font-bold uppercase">
      демо — таких данных нет ни в одном сервисе
    </span>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div
        v-for="metric in metrics"
        :key="metric.label"
        class="bg-surface-container-lowest p-5 rounded-DEFAULT shadow-sm flex items-center gap-4"
      >
        <div class="w-12 h-12 rounded-full flex items-center justify-center shrink-0" :class="[metric.bg, metric.fg]">
          <span class="material-symbols-outlined text-[24px]">{{ metric.icon }}</span>
        </div>
        <div class="flex flex-col">
          <span class="font-headline-md text-headline-md font-bold text-on-surface">{{ metric.value }}</span>
          <span class="font-body-sm text-body-sm text-on-surface-variant">{{ metric.label }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
