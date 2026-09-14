<script setup>
defineProps({
  formNumber: { type: String, default: 'Полевой формуляр № 1941-ОМ-214' },
  title: { type: String, default: 'Неизвестный десантник 9-й воздушно-десантной бригады' },
  dateAndPlace: { type: String, default: 'Октябрь 1941 г. • Бои на шоссе Орёл — Мценск' },
})
</script>

<template>
  <div class="flex flex-col gap-2">
    <div class="flex items-center justify-between flex-wrap gap-2">
      <span class="px-3 py-1 rounded-full bg-tertiary-fixed text-on-tertiary-fixed font-label-sm text-label-sm font-bold tracking-wide uppercase">
        {{ formNumber }}
      </span>
      <span class="flex items-center gap-1.5 font-label-sm text-label-sm text-secondary font-bold">
        <span class="w-2 h-2 rounded-full bg-secondary" />
        Запись обновляется онлайн
      </span>
    </div>
    <h1 class="font-headline-lg text-headline-lg text-on-surface font-extrabold tracking-tight leading-snug">{{ title }}</h1>
    <div class="flex items-center gap-2 text-on-surface-variant font-label-md text-label-md">
      <span class="material-symbols-outlined text-[18px] text-primary">calendar_today</span>
      <span>{{ dateAndPlace }}</span>
    </div>
  </div>
</template>
