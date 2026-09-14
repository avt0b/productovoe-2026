<script setup>
import { ref } from 'vue'
import LeafletMap from '@shared/components/LeafletMap.vue'

const center = [53.145, 36.47]

const markers = [
  { lat: 53.145, lng: 36.47, title: 'Выс. 214 • Останки бойца', subtitle: '9-я ВДБр • Смертный медальон' },
  { lat: 53.15, lng: 36.46, title: 'Окопный узел В-12 (Проверка)' },
  { lat: 53.14, lng: 36.48, title: 'Блиндаж сапёров 4-й тбр' },
  { lat: 53.135, lng: 36.475, title: 'Засада Т-34 у р. Зуша' },
]

const legend = [
  { label: 'Текущий раскоп (Выс. 214)', dot: 'bg-primary' },
  { label: 'Требует разведки', dot: 'bg-tertiary' },
  { label: 'Архивно верифицировано', dot: 'bg-secondary' },
]

const mapRef = ref(null)
</script>

<template>
  <div class="relative bg-surface-container-lowest rounded-lg shadow-md overflow-hidden min-h-[640px]">
    <div class="absolute inset-0 z-0">
      <LeafletMap ref="mapRef" :center="center" :zoom="14" :markers="markers" />
    </div>

    <div class="absolute top-3 left-3 right-3 z-10 flex items-center justify-between gap-3 p-3 bg-surface-container-lowest/90 backdrop-blur-md rounded-DEFAULT shadow-sm">
      <div class="flex items-center gap-3 min-w-0">
        <div class="w-8 h-8 rounded-full bg-secondary-container text-on-secondary-container flex items-center justify-center font-bold text-label-md shrink-0">
          A14
        </div>
        <div class="min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="font-headline-sm text-headline-sm text-on-surface font-bold">Орловско-Мценский рубеж</span>
            <span class="px-2 py-0.5 rounded-full bg-error-container text-on-error-container font-label-sm text-label-sm font-extrabold">
              Сектор боёв
            </span>
          </div>
          <p class="font-body-sm text-body-sm text-on-surface-variant truncate">Квадраты А-14, В-12 • Шоссе Орёл — Тула • Высота 214</p>
        </div>
      </div>
      <div class="flex items-center gap-1.5 shrink-0">
        <button
          class="w-8 h-8 rounded-full bg-surface-container-low hover:bg-surface-container text-on-surface flex items-center justify-center transition-colors"
          title="Приблизить"
          @click="mapRef?.zoomIn()"
        >
          <span class="material-symbols-outlined text-[18px]">add</span>
        </button>
        <button
          class="w-8 h-8 rounded-full bg-surface-container-low hover:bg-surface-container text-on-surface flex items-center justify-center transition-colors"
          title="Отдалить"
          @click="mapRef?.zoomOut()"
        >
          <span class="material-symbols-outlined text-[18px]">remove</span>
        </button>
      </div>
    </div>

    <div class="absolute bottom-3 left-3 right-3 z-10 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-3 bg-surface-container-lowest/90 backdrop-blur-md rounded-DEFAULT shadow-sm">
      <div class="flex items-center gap-4 flex-wrap text-on-surface-variant font-label-sm text-label-sm">
        <div v-for="item in legend" :key="item.label" class="flex items-center gap-1.5">
          <span class="w-2.5 h-2.5 rounded-full" :class="item.dot" />
          <span>{{ item.label }}</span>
        </div>
      </div>
      <div class="flex items-center justify-between sm:justify-end gap-2 text-on-surface font-label-sm text-label-sm bg-surface-container-low px-3 py-1.5 rounded-full font-mono">
        <span class="material-symbols-outlined text-[16px] text-primary">my_location</span>
        <span>53°14'28" N • 36°28'12" E</span>
      </div>
    </div>
  </div>
</template>
