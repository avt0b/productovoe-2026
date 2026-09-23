<script setup>
import SmartImage from '@shared/components/SmartImage.vue'

// Ни в одном сервисе нет сущности «семейное древо» — демо-заглушка целиком,
// имена и фото ниже вымышленные, не подставляются из данных пользователя.
const heroes = [
  {
    name: 'Сержант Воронов А. Г.',
    tag: 'Погиб в бою',
    tagClass: 'bg-primary-fixed text-on-primary-fixed',
    years: '1919 – 1944 • 120-й стрелковый полк, Орловский рубеж',
    note: 'Подтверждено в ОБД «Мемориал»',
    noteIcon: 'verified',
    noteClass: 'text-secondary',
    photoUrl: 'https://loremflickr.com/128/128/soldier,vintage,portrait?lock=102',
  },
  {
    name: 'Рядовой Смирнов П. И.',
    tag: 'Ветеран',
    tagClass: 'bg-secondary-fixed text-on-secondary-fixed',
    years: '1923 – 1989 • Связист, 3-я армия, Брянский фронт',
    note: 'Медаль «За отвагу», Орден Красной Звезды',
    noteIcon: 'military_tech',
    noteClass: 'text-tertiary',
    photoUrl: 'https://loremflickr.com/128/128/veteran,portrait,elderly?lock=103',
  },
]
</script>

<template>
  <div class="bg-surface-container-lowest p-6 rounded-DEFAULT shadow-sm flex flex-col">
    <div class="flex items-center justify-between gap-4 mb-6">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-full bg-secondary-container text-on-secondary-container flex items-center justify-center">
          <span class="material-symbols-outlined text-[20px]">diversity_3</span>
        </div>
        <div class="flex flex-col">
          <h2 class="font-headline-sm text-headline-sm font-bold text-on-surface flex items-center gap-2 flex-wrap">
            Семейное древо и герои рода
            <span class="px-2 py-0.5 rounded-full bg-surface-container-high text-on-surface-variant font-label-sm text-label-sm font-bold normal-case">
              демо — такой сущности нет ни в одном сервисе
            </span>
          </h2>
          <span class="font-body-sm text-body-sm text-on-surface-variant">Пример того, как это могло бы выглядеть</span>
        </div>
      </div>
      <button
        class="bg-secondary-fixed hover:bg-secondary-fixed-dim text-on-secondary-fixed font-label-md text-label-md font-bold px-4 py-2 rounded-full transition-all flex items-center gap-1.5 shadow-sm"
      >
        <span class="material-symbols-outlined text-[18px]">add</span>
        <span class="hidden sm:inline">Добавить предка</span>
      </button>
    </div>

    <div class="flex flex-col gap-4">
      <div
        v-for="hero in heroes"
        :key="hero.name"
        class="bg-surface-container-low p-4 rounded-DEFAULT flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:bg-surface-container transition-colors"
      >
        <div class="flex items-center gap-4">
          <div class="w-16 h-16 rounded-DEFAULT overflow-hidden bg-surface-container-high shrink-0 shadow-sm">
            <SmartImage :src="hero.photoUrl" icon="portrait" />
          </div>
          <div class="flex flex-col">
            <div class="flex items-center gap-2">
              <h3 class="font-headline-sm text-headline-sm text-on-surface font-bold">{{ hero.name }}</h3>
              <span class="text-[11px] font-bold px-2 py-0.5 rounded-full uppercase" :class="hero.tagClass">
                {{ hero.tag }}
              </span>
            </div>
            <p class="font-body-sm text-body-sm text-on-surface-variant mt-0.5">{{ hero.years }}</p>
            <div class="flex items-center gap-2 mt-2">
              <span class="material-symbols-outlined text-[16px]" :class="hero.noteClass">{{ hero.noteIcon }}</span>
              <span class="font-label-sm text-label-sm font-bold" :class="hero.noteClass">{{ hero.note }}</span>
            </div>
          </div>
        </div>
        <button
          class="bg-surface-container-lowest text-on-surface hover:bg-surface-container-high px-3.5 py-1.5 rounded-full font-label-sm text-label-sm font-bold shadow-sm flex items-center gap-1 shrink-0"
        >
          <span>Карточка</span>
          <span class="material-symbols-outlined text-[16px]">chevron_right</span>
        </button>
      </div>
    </div>
  </div>
</template>
