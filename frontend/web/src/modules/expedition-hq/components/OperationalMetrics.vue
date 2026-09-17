<script setup>
const metrics = [
  {
    icon: 'person_search',
    iconWrap: 'bg-primary/10 text-primary',
    tag: '+4 за неделю',
    tagClass: 'text-primary bg-primary/10',
    value: '14',
    title: 'Бойцов поднято',
    text: 'Останки обнаружены в санитарных захоронениях и воронках рубежа',
  },
  {
    icon: 'military_tech',
    iconWrap: 'bg-secondary/10 text-secondary',
    tag: 'Церемония',
    tagClass: 'text-secondary bg-secondary-container',
    value: '3',
    title: 'Преданы земле',
    text: 'С воинскими почестями на Кривцовском мемориале славы',
  },
  {
    icon: 'badge',
    iconWrap: 'bg-tertiary/10 text-tertiary',
    tag: 'Экспертиза',
    tagClass: 'text-tertiary bg-tertiary-fixed',
    value: '2',
    title: 'Имени установлено',
    text: 'Бакелитовые капсулы ЛОЗ переданы экспертам-криминалистам',
  },
]
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
    <div
      v-for="metric in metrics"
      :key="metric.title"
      class="bg-surface-container-lowest rounded-DEFAULT p-6 shadow-sm flex flex-col justify-between hover:shadow-md transition-shadow"
    >
      <div class="flex items-center justify-between mb-4">
        <span class="w-12 h-12 rounded-full flex items-center justify-center" :class="metric.iconWrap">
          <span class="material-symbols-outlined text-[26px]">{{ metric.icon }}</span>
        </span>
        <span
          class="font-label-sm text-label-sm uppercase font-bold px-2.5 py-1 rounded-full"
          :class="metric.tagClass"
        >
          {{ metric.tag }}
        </span>
      </div>
      <div class="flex flex-col">
        <span class="font-headline-xl text-headline-xl text-on-surface tracking-tight leading-none mb-2">
          {{ metric.value }}
        </span>
        <span class="font-headline-sm text-headline-sm text-on-surface font-bold">{{ metric.title }}</span>
        <p class="font-body-sm text-body-sm text-outline mt-1">{{ metric.text }}</p>
      </div>
    </div>
  </div>
</template>
