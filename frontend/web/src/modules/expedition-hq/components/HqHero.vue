<script setup>
defineProps({
  seasonBadge: { type: String, default: 'Экспедиционный сезон открыт' },
  briefRef: { type: String, default: 'Сводка штаба #08-24' },
  title: { type: String, default: 'Вахта Памяти 2024: Полевой Штаб' },
  quote: { type: String, default: '«Война не окончена, пока не похоронен последний солдат»' },
  squadCount: { type: String, default: '12 отрядов на линии' },
  squadLocation: { type: String, default: 'Орловская дуга, Болховский сектор' },
})

const avatars = [
  { label: 'ОР', bg: 'bg-secondary-fixed', fg: 'text-on-secondary-fixed' },
  { label: 'ВЫ', bg: 'bg-primary-fixed', fg: 'text-on-primary-fixed' },
  { label: 'РБ', bg: 'bg-tertiary-fixed', fg: 'text-on-tertiary-fixed' },
  { label: '+9', bg: 'bg-surface-container-high', fg: 'text-on-surface' },
]
</script>

<template>
  <section class="w-full py-8">
    <div
      class="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 bg-surface-container-lowest rounded-lg p-8 shadow-sm relative overflow-hidden"
    >
      <div class="absolute -right-16 -top-16 w-64 h-64 bg-primary/5 rounded-full blur-3xl pointer-events-none" />

      <div class="flex flex-col gap-2 max-w-2xl z-10">
        <div class="flex items-center gap-3">
          <span
            class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-secondary-container text-on-secondary-container font-label-sm text-label-sm uppercase tracking-wider"
          >
            <span class="w-2 h-2 rounded-full bg-secondary" />
            {{ seasonBadge }}
          </span>
          <span class="font-label-sm text-label-sm text-outline">{{ briefRef }}</span>
        </div>
        <h1 class="font-headline-xl text-headline-xl text-on-surface tracking-tight">{{ title }}</h1>
        <p class="font-body-lg text-body-lg text-on-surface-variant italic">{{ quote }}</p>
      </div>

      <div class="flex items-center gap-4 z-10 w-full sm:w-auto">
        <div class="flex -space-x-3 items-center">
          <div
            v-for="avatar in avatars"
            :key="avatar.label"
            class="w-10 h-10 rounded-full flex items-center justify-center text-label-md font-label-md font-bold shadow-sm"
            :class="[avatar.bg, avatar.fg]"
          >
            {{ avatar.label }}
          </div>
        </div>
        <div class="flex flex-col">
          <span class="font-label-md text-label-md text-on-surface font-bold">{{ squadCount }}</span>
          <span class="font-body-sm text-body-sm text-outline">{{ squadLocation }}</span>
        </div>
      </div>
    </div>
  </section>
</template>
