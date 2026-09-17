<script setup>
defineProps({
  unitBadge: { type: String, default: 'Гвардейский взвод' },
  tokenBadge: { type: String, default: 'Личный жетон № 714-Б' },
  fullName: { type: String, default: 'Сержант Алексей Григорьевич Воронов' },
  lifespan: { type: String, default: '15 марта 1920 — 18 февраля 1942 (21 год)' },
  award: { type: String, default: 'Медаль «За отвагу»' },
  awardOrder: { type: String, default: 'Приказ № 014 от 22.01.1942' },
  position: { type: String, default: 'Командир стрелкового отделения' },
  unit: { type: String, default: '137-я стрелковая дивизия (409 СП)' },
  draftPlace: { type: String, default: 'Орловская губ., Елецкий РВК' },
  draftDate: { type: String, default: 'Призван 10 октября 1940 г.' },
  lastStandTag: { type: String, default: 'Высота 214.6' },
  lastStandTitle: { type: String, default: 'Оборона рубежа реки Ока • Болховское направление' },
  lastStandText: {
    type: String,
    default:
      'Погиб при отражении танковой контратаки на Кривцовском плацдарме. Имя увековечено на мраморных плитах братской могилы Кривцовского мемориального комплекса.',
  },
  camoFund: { type: String, default: 'Фонд ЦАМО 500/12480/41' },
  upkNumber: { type: String, default: 'УПК № 0941824' },
})
</script>

<template>
  <div class="bg-surface-container-lowest rounded-lg p-7 shadow-sm flex flex-col gap-6">
    <div
      class="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-5 bg-surface-container-low/40 -mx-7 -mt-7 p-7 rounded-t-lg"
    >
      <div class="flex flex-col gap-1.5">
        <div class="flex items-center gap-2 flex-wrap">
          <span
            class="px-2.5 py-0.5 rounded-full bg-primary-fixed text-on-primary-fixed font-label-sm text-label-sm font-bold uppercase tracking-wider"
          >
            {{ unitBadge }}
          </span>
          <span class="px-2.5 py-0.5 rounded-full bg-surface-container-high text-on-surface-variant font-label-sm text-label-sm font-bold">
            {{ tokenBadge }}
          </span>
        </div>
        <h1 class="font-headline-lg text-headline-lg text-on-surface tracking-tight mt-1">{{ fullName }}</h1>
        <span class="font-headline-sm text-headline-sm text-on-surface-variant font-medium">{{ lifespan }}</span>
      </div>

      <div class="flex flex-col items-center sm:items-end shrink-0">
        <div class="inline-flex items-center gap-2 px-3.5 py-2 rounded-DEFAULT bg-tertiary-fixed text-on-tertiary-fixed shadow-sm">
          <span class="material-symbols-outlined text-tertiary text-[22px]" style="font-variation-settings: 'FILL' 1">
            military_tech
          </span>
          <div class="flex flex-col text-left">
            <span class="font-label-sm text-label-sm text-on-tertiary-fixed-variant uppercase">Награда</span>
            <span class="font-label-md text-label-md font-bold text-on-tertiary-fixed leading-none">{{ award }}</span>
          </div>
        </div>
        <span class="font-label-sm text-label-sm text-outline mt-1.5">{{ awardOrder }}</span>
      </div>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div class="bg-surface-container-low rounded-DEFAULT p-4 flex items-start gap-3">
        <div class="w-9 h-9 rounded-full bg-surface-container-highest flex items-center justify-center text-primary shrink-0">
          <span class="material-symbols-outlined text-[20px]">shield</span>
        </div>
        <div class="flex flex-col">
          <span class="font-label-sm text-label-sm text-on-surface-variant uppercase">Воинское подразделение</span>
          <span class="font-label-md text-label-md text-on-surface font-bold mt-0.5">{{ position }}</span>
          <span class="font-body-sm text-body-sm text-secondary font-medium">{{ unit }}</span>
        </div>
      </div>
      <div class="bg-surface-container-low rounded-DEFAULT p-4 flex items-start gap-3">
        <div class="w-9 h-9 rounded-full bg-surface-container-highest flex items-center justify-center text-secondary shrink-0">
          <span class="material-symbols-outlined text-[20px]">pin_drop</span>
        </div>
        <div class="flex flex-col">
          <span class="font-label-sm text-label-sm text-on-surface-variant uppercase">Место призыва</span>
          <span class="font-label-md text-label-md text-on-surface font-bold mt-0.5">{{ draftPlace }}</span>
          <span class="font-body-sm text-body-sm text-on-surface-variant">{{ draftDate }}</span>
        </div>
      </div>
      <div class="bg-surface-container-low rounded-DEFAULT p-4 flex items-start gap-3 sm:col-span-2">
        <div class="w-9 h-9 rounded-full bg-surface-container-highest flex items-center justify-center text-tertiary shrink-0">
          <span class="material-symbols-outlined text-[20px]">explore</span>
        </div>
        <div class="flex flex-col flex-1">
          <div class="flex items-center justify-between">
            <span class="font-label-sm text-label-sm text-on-surface-variant uppercase">Боевой путь и последний рубеж</span>
            <span class="font-label-sm text-label-sm bg-secondary-container text-on-secondary-container px-2 py-0.5 rounded-full font-bold">
              {{ lastStandTag }}
            </span>
          </div>
          <span class="font-label-md text-label-md text-on-surface font-bold mt-0.5">{{ lastStandTitle }}</span>
          <p class="font-body-sm text-body-sm text-on-surface-variant mt-1">{{ lastStandText }}</p>
        </div>
      </div>
    </div>

    <div class="flex items-center justify-between pt-2">
      <div class="flex items-center gap-4 text-outline font-label-sm text-label-sm">
        <span class="flex items-center gap-1">
          <span class="material-symbols-outlined text-[16px]">folder_open</span>
          {{ camoFund }}
        </span>
        <span class="flex items-center gap-1">
          <span class="material-symbols-outlined text-[16px]">fingerprint</span>
          {{ upkNumber }}
        </span>
      </div>
      <button class="font-label-md text-label-md text-primary font-bold hover:underline flex items-center gap-1">
        <span>Полная выписка архива</span>
        <span class="material-symbols-outlined text-[16px]">arrow_forward</span>
      </button>
    </div>
  </div>
</template>
