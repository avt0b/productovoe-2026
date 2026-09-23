<script setup>
import { computed, defineAsyncComponent } from 'vue'

// Модалка открывается из карточек в профиле и на вкладке экскурсий —
// оба места лежат в основном бандле (MyExcursions), а Leaflet — тяжёлая
// библиотека (~150 КБ). Асинхронный импорт держит её в отдельном чанке,
// который подгружается только когда модалку реально открыли.
const LeafletMap = defineAsyncComponent(() => import('@shared/components/LeafletMap.vue'))

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  excursion: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue'])

// core/models/excursion.py: ExcursionStatus
const STATUS_META = {
  scheduled: { label: 'Идёт запись', class: 'bg-secondary-container text-on-secondary-container' },
  gathering: { label: 'Идёт сбор группы', class: 'bg-tertiary-fixed text-on-tertiary-fixed' },
  finished: { label: 'Прошла', class: 'bg-secondary-fixed text-on-secondary-fixed' },
  cancelled: { label: 'Отменена', class: 'bg-error-container text-on-error-container' },
}

const markers = computed(() => {
  if (!props.excursion) return []
  return [
    {
      id: props.excursion.id,
      lat: props.excursion.lat,
      lng: props.excursion.lon,
      title: props.excursion.title,
      subtitle: props.excursion.place_name,
      icon: 'groups_3',
      badgeClass: 'bg-secondary',
      tailClass: 'border-t-secondary',
    },
  ]
})

function formatDate(iso) {
  return new Date(iso).toLocaleString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function close() {
  emit('update:modelValue', false)
}
</script>

<template>
  <div
    v-if="modelValue && excursion"
    class="fixed inset-0 z-50 bg-on-background/40 backdrop-blur-sm flex items-center justify-center p-4"
    @click.self="close"
  >
    <div class="bg-surface-container-lowest rounded-lg max-w-2xl w-full shadow-2xl flex flex-col overflow-hidden max-h-[90vh]">
      <div class="flex items-center justify-between p-5 border-b border-surface-container-high shrink-0">
        <div class="flex flex-col min-w-0">
          <span class="font-headline-sm text-headline-sm text-on-surface font-bold truncate">{{ excursion.title }}</span>
          <span class="font-body-sm text-body-sm text-on-surface-variant truncate">
            {{ excursion.place_name || 'место уточняется' }}
          </span>
        </div>
        <button
          class="w-8 h-8 rounded-full bg-surface-container hover:bg-surface-container-high text-on-surface flex items-center justify-center transition-colors shrink-0"
          @click="close"
        >
          <span class="material-symbols-outlined text-[18px]">close</span>
        </button>
      </div>

      <div class="relative h-80 bg-surface-container overflow-hidden shrink-0">
        <LeafletMap :center="[excursion.lat, excursion.lon]" :zoom="13" :markers="markers" />
      </div>

      <div class="p-5 flex flex-col gap-3">
        <div class="flex items-center gap-3 flex-wrap">
          <span
            class="px-2.5 py-1 rounded-full font-label-sm text-label-sm font-bold flex items-center gap-1"
            :class="STATUS_META[excursion.status]?.class ?? 'bg-surface-container text-on-surface-variant'"
          >
            {{ STATUS_META[excursion.status]?.label ?? excursion.status }}
          </span>
          <span class="font-label-sm text-label-sm text-on-surface-variant flex items-center gap-1">
            <span class="material-symbols-outlined text-[16px]">event</span>
            {{ formatDate(excursion.starts_at) }}
          </span>
          <span class="font-label-sm text-label-sm text-on-surface-variant flex items-center gap-1">
            <span class="material-symbols-outlined text-[16px]">group</span>
            {{ excursion.registered_count }} из {{ excursion.capacity }}
          </span>
        </div>
        <p v-if="excursion.description" class="font-body-sm text-body-sm text-on-surface-variant">
          {{ excursion.description }}
        </p>
      </div>
    </div>
  </div>
</template>
