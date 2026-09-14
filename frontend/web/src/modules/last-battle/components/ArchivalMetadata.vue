<script setup></script>

<template>
  <div class="flex flex-col gap-2.5">
    <div class="bg-surface-container-low p-3.5 rounded-DEFAULT flex items-start gap-3">
      <span class="material-symbols-outlined text-primary text-[22px] shrink-0 mt-0.5">location_on</span>
      <div class="flex flex-col min-w-0">
        <span class="font-label-sm text-label-sm text-on-surface-variant font-bold uppercase tracking-wider">Точные полевые координаты</span>
        <span class="font-body-md text-body-md text-on-surface font-semibold truncate">
          53°14'28" N, 36°28'12" E (высота 214)
        </span>
        <span class="font-body-sm text-body-sm text-on-surface-variant">
          Левый фланг обороны 4-й танковой бригады генерала Катукова
        </span>
      </div>
    </div>

    <div class="bg-surface-container-low p-3.5 rounded-DEFAULT flex items-start gap-3">
      <span class="material-symbols-outlined text-tertiary text-[22px] shrink-0 mt-0.5">menu_book</span>
      <div class="flex flex-col min-w-0">
        <span class="font-label-sm text-label-sm text-on-surface-variant font-bold uppercase tracking-wider">Архивный источник</span>
        <span class="font-body-md text-body-md text-on-surface font-semibold">Книга Памяти Орловской области</span>
        <span class="font-body-sm text-body-sm text-on-surface-variant">
          Том 5, стр. 182 • Сводка безвозвратных потерь 201-го вдб
        </span>
      </div>
    </div>

    <div class="bg-surface-container p-3.5 rounded-DEFAULT flex items-start gap-3">
      <span class="material-symbols-outlined text-primary text-[22px] shrink-0 mt-0.5">fingerprint</span>
      <div class="flex flex-col min-w-0">
        <div class="flex items-center gap-2">
          <span class="font-label-sm text-label-sm text-primary font-bold uppercase tracking-wider">Статус экспертизы</span>
          <span class="px-2 py-0.2 rounded-full bg-primary-fixed text-on-primary-fixed font-label-sm text-label-sm font-bold">
            В лаборатории
          </span>
        </div>
        <span class="font-body-md text-body-md text-on-surface font-bold">
          Найден смертный медальон (эбонитовая капсула)
        </span>
        <p class="font-body-sm text-body-sm text-on-surface-variant mt-0.5">
          Бумажный вкладыш частично развернут экспертами в Орле. Первые буквы фамилии: «...МОРОЗ...», год рожд. 1919.
        </p>
      </div>
    </div>
  </div>
</template>
