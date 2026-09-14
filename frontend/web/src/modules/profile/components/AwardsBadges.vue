<script setup>
const badges = [
  { icon: 'explore', title: '10 км рубежей', subtitle: 'Пройдено пешком', date: '14 мая 2023', bg: 'bg-secondary', fg: 'text-on-secondary', accent: 'text-secondary' },
  { icon: 'radar', title: 'Юный радист', subtitle: 'Шифр расшифрован', date: '22 авг 2023', bg: 'bg-primary', fg: 'text-on-primary', accent: 'text-primary' },
  { icon: 'menu_book', title: 'Хранитель истории', subtitle: '3 очерка сдано', date: '10 апр 2024', bg: 'bg-tertiary', fg: 'text-on-tertiary', accent: 'text-tertiary' },
  { icon: 'share_location', title: 'Мастер карт', subtitle: 'Сетка рубежа', date: '3 окт 2024', bg: 'bg-secondary-fixed', fg: 'text-on-secondary-fixed', accent: 'text-secondary' },
]
</script>

<template>
  <div class="bg-surface-container-lowest p-6 rounded-DEFAULT shadow-sm flex flex-col">
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-full bg-tertiary-fixed text-on-tertiary-fixed flex items-center justify-center">
          <span class="material-symbols-outlined text-[20px]">military_tech</span>
        </div>
        <div class="flex flex-col">
          <h2 class="font-headline-sm text-headline-sm font-bold text-on-surface">Награды и полевые значки</h2>
          <span class="font-body-sm text-body-sm text-on-surface-variant">Открыто 4 из 12 знаков отличия</span>
        </div>
      </div>
      <span class="font-label-sm text-label-sm bg-surface-container-high text-on-surface-variant px-3 py-1 rounded-full font-bold">
        33% завершено
      </span>
    </div>

    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
      <div
        v-for="badge in badges"
        :key="badge.title"
        class="bg-surface-container-low p-4 rounded-DEFAULT flex flex-col items-center text-center group hover:bg-surface-container transition-all"
      >
        <div
          class="w-14 h-14 rounded-full flex items-center justify-center mb-3 shadow-md group-hover:scale-105 transition-transform"
          :class="[badge.bg, badge.fg]"
        >
          <span class="material-symbols-outlined text-[28px]">{{ badge.icon }}</span>
        </div>
        <span class="font-headline-sm text-[15px] font-bold text-on-surface leading-snug">{{ badge.title }}</span>
        <span class="font-label-sm text-label-sm font-semibold mt-1" :class="badge.accent">{{ badge.subtitle }}</span>
        <span class="font-body-sm text-[11px] text-on-surface-variant mt-2 bg-surface-container-lowest px-2 py-0.5 rounded-full">
          {{ badge.date }}
        </span>
      </div>
    </div>

    <div class="mt-4 pt-4 bg-surface-container-low/50 rounded-DEFAULT p-3.5 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <span class="material-symbols-outlined text-on-surface-variant text-[22px]">lock</span>
        <div class="flex flex-col">
          <span class="font-label-md text-label-md font-bold text-on-surface">Следующий значок: «Ночной дозор рубежа»</span>
          <span class="font-body-sm text-body-sm text-on-surface-variant">Требуется завершить экспедицию в вечернее время</span>
        </div>
      </div>
      <span class="font-label-sm text-label-sm font-bold text-primary cursor-pointer hover:underline whitespace-nowrap">
        Все 12 наград →
      </span>
    </div>
  </div>
</template>
