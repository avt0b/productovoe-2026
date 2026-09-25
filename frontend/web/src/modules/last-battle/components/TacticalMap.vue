<script setup>
import { computed, ref } from 'vue'
import LeafletMap from '@shared/components/LeafletMap.vue'

const props = defineProps({
  points: { type: Array, default: () => [] },
  selectedId: { type: String, default: null },
})
const emit = defineEmits(['select'])

const FALLBACK_CENTER = [53.145, 36.47]

const STATUS_META = {
  discovered: {
    dot: 'bg-tertiary',
    label: 'Требует разведки',
    icon: 'search',
    badgeClass: 'bg-tertiary',
    tailClass: 'border-t-tertiary',
  },
  archive_confirmed: {
    dot: 'bg-primary',
    label: 'Подтверждено архивом',
    icon: 'verified',
    badgeClass: 'bg-primary',
    tailClass: 'border-t-primary',
  },
  remains_raised: {
    dot: 'bg-secondary',
    label: 'Останки подняты',
    icon: 'military_tech',
    badgeClass: 'bg-secondary',
    tailClass: 'border-t-secondary',
  },
}

const legend = Object.values(STATUS_META)

const markers = computed(() =>
  props.points.map((p) => ({
    id: p.id,
    lat: p.lat,
    lng: p.lon,
    title: p.soldier_name || 'Неизвестный боец',
    subtitle: [p.unit, STATUS_META[p.status]?.label].filter(Boolean).join(' • '),
    icon: STATUS_META[p.status]?.icon ?? 'location_on',
    badgeClass: STATUS_META[p.status]?.badgeClass,
    tailClass: STATUS_META[p.status]?.tailClass,
  })),
)

const center = computed(() => {
  const point = props.points.find((p) => p.id === props.selectedId)
  return point ? [point.lat, point.lon] : FALLBACK_CENTER
})

const mapRef = ref(null)
</script>

<template>
  <div class="relative bg-surface-container-lowest rounded-lg shadow-md overflow-hidden min-h-[640px]">
    <div class="absolute inset-0 z-0">
      <LeafletMap
        ref="mapRef"
        :center="center"
        :zoom="13"
        :markers="markers"
        @marker-click="emit('select', $event)"
      />
    </div>

    <div class="absolute top-3 left-3 right-3 z-10 flex items-center justify-between gap-3 p-3 bg-surface-container-lowest/90 backdrop-blur-md rounded-DEFAULT shadow-sm">
      <div class="flex items-center gap-3 min-w-0">
        <div class="w-8 h-8 rounded-full bg-secondary-container text-on-secondary-container flex items-center justify-center font-bold text-label-md shrink-0">
          {{ points.length }}
        </div>
        <div class="min-w-0">
          <span class="font-headline-sm text-headline-sm text-on-surface font-bold">Карта «Последний бой»</span>
          <p class="font-body-sm text-body-sm text-on-surface-variant truncate">
            Орловская область • клик по метке открывает досье
          </p>
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
    </div>
  </div>
</template>
