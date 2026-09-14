<script setup>
import { ref } from 'vue'

const filters = [
  { id: 'checking', label: 'Обнаружено (проверка)', count: 12, dot: 'bg-tertiary animate-pulse' },
  { id: 'confirmed', label: 'Подтверждено архивом', count: 48, dot: 'bg-primary-container' },
  { id: 'reburied', label: 'Останки подняты / Увековечено', count: 142, dot: 'bg-secondary' },
]

const activeFilter = ref('checking')
const mapLayer = ref('topo')
</script>

<template>
  <section class="mb-6 flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4">
    <div class="flex items-center gap-2 overflow-x-auto pb-1 lg:pb-0">
      <button
        v-for="filter in filters"
        :key="filter.id"
        class="flex items-center gap-2 px-4 py-2 rounded-full shadow-sm transition-transform hover:scale-[1.02] shrink-0"
        :class="
          activeFilter === filter.id
            ? 'bg-tertiary-fixed text-on-tertiary-fixed'
            : 'bg-surface-container-lowest text-on-surface hover:bg-surface-container'
        "
        @click="activeFilter = filter.id"
      >
        <span class="w-2.5 h-2.5 rounded-full" :class="filter.dot" />
        <span class="font-label-md text-label-md" :class="activeFilter === filter.id ? 'font-bold' : 'font-medium'">
          {{ filter.label }}
        </span>
        <span
          class="px-2 py-0.5 rounded-full font-label-sm text-label-sm"
          :class="
            activeFilter === filter.id
              ? 'bg-surface-container-lowest/80 text-on-tertiary-fixed font-extrabold'
              : 'bg-surface-container text-on-surface-variant'
          "
        >
          {{ filter.count }}
        </span>
      </button>
    </div>

    <div class="flex items-center gap-3 self-end lg:self-center">
      <div class="bg-surface-container-lowest rounded-full p-1 shadow-sm flex items-center">
        <button
          class="px-3.5 py-1.5 rounded-full font-label-sm text-label-sm flex items-center gap-1.5 transition-all"
          :class="mapLayer === 'topo' ? 'bg-secondary-container text-on-secondary-container font-bold' : 'text-on-surface-variant font-semibold'"
          @click="mapLayer = 'topo'"
        >
          <span class="material-symbols-outlined text-[16px]">map</span>
          <span>Топокарта РККА</span>
        </button>
        <button
          class="px-3.5 py-1.5 rounded-full font-label-sm text-label-sm flex items-center gap-1.5 transition-all"
          :class="mapLayer === 'sat' ? 'bg-secondary-container text-on-secondary-container font-bold' : 'text-on-surface-variant font-semibold'"
          @click="mapLayer = 'sat'"
        >
          <span class="material-symbols-outlined text-[16px]">satellite_alt</span>
          <span>Спутник</span>
        </button>
      </div>
      <button class="h-9 px-3 rounded-full bg-surface-container-lowest hover:bg-surface-container text-on-surface font-label-sm text-label-sm flex items-center gap-1.5 shadow-sm transition-colors">
        <span class="material-symbols-outlined text-secondary text-[18px]">layers</span>
        <span>Слои 1941</span>
      </button>
    </div>
  </section>
</template>
