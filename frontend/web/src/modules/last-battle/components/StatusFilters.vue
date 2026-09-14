<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  // Полный список точек текущего фильтра — используется только чтобы
  // показать актуальный счётчик на активной вкладке (map_service не отдаёт
  // счётчики по всем статусам одним запросом).
  countsSource: { type: Array, default: () => [] },
})
const emit = defineEmits(['change'])

// id соответствуют enum LastStandStatus в map_service (core/models/last_stand.py)
const filters = [
  { id: null, label: 'Все точки', dot: 'bg-outline' },
  { id: 'discovered', label: 'Обнаружено (проверка)', dot: 'bg-tertiary animate-pulse' },
  { id: 'archive_confirmed', label: 'Подтверждено архивом', dot: 'bg-primary-container' },
  { id: 'remains_raised', label: 'Останки подняты / Увековечено', dot: 'bg-secondary' },
]

const activeFilter = ref(null)

const activeCount = computed(() => props.countsSource.length)

function select(id) {
  activeFilter.value = id
  emit('change', id)
}
</script>

<template>
  <section class="mb-6 flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4">
    <div class="flex items-center gap-2 overflow-x-auto pb-1 lg:pb-0">
      <button
        v-for="filter in filters"
        :key="filter.id ?? 'all'"
        class="flex items-center gap-2 px-4 py-2 rounded-full shadow-sm transition-transform hover:scale-[1.02] shrink-0"
        :class="
          activeFilter === filter.id
            ? 'bg-tertiary-fixed text-on-tertiary-fixed'
            : 'bg-surface-container-lowest text-on-surface hover:bg-surface-container'
        "
        @click="select(filter.id)"
      >
        <span class="w-2.5 h-2.5 rounded-full" :class="filter.dot" />
        <span class="font-label-md text-label-md" :class="activeFilter === filter.id ? 'font-bold' : 'font-medium'">
          {{ filter.label }}
        </span>
        <span
          v-if="activeFilter === filter.id"
          class="px-2 py-0.5 rounded-full font-label-sm text-label-sm bg-surface-container-lowest/80 text-on-tertiary-fixed font-extrabold"
        >
          {{ activeCount }}
        </span>
      </button>
    </div>

    <div class="flex items-center gap-3 self-end lg:self-center">
      <span class="font-label-sm text-label-sm text-on-surface-variant">
        Данные из <code class="font-mono">map_service</code>, слой «ВОВ» пока не подключён
      </span>
    </div>
  </section>
</template>
