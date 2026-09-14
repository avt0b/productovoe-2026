<script setup>
defineProps({
  title: { type: String, default: 'Тропа памяти: семейные маршруты' },
  text: {
    type: String,
    default:
      'Пешие маршруты по местам боёв с квестами для детей и родителей: загадки, аудиоспектакли и точки на карте, привязанные к реальным событиям 1941–1943 годов.',
  },
})
</script>

<template>
  <section class="w-full py-8">
    <div class="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 bg-surface-container-lowest rounded-lg p-8 shadow-sm relative overflow-hidden">
      <div class="absolute -right-16 -top-16 w-64 h-64 bg-secondary/10 rounded-full blur-3xl pointer-events-none" />
      <div class="flex flex-col gap-2 max-w-2xl z-10">
        <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-secondary-container text-on-secondary-container font-label-sm text-label-sm uppercase tracking-wider w-fit">
          <span class="material-symbols-outlined text-[14px]">family_restroom</span>
          Семейный режим
        </span>
        <h1 class="font-headline-xl text-headline-xl text-on-surface tracking-tight">{{ title }}</h1>
        <p class="font-body-lg text-body-lg text-on-surface-variant">{{ text }}</p>
      </div>
    </div>
  </section>
</template>
