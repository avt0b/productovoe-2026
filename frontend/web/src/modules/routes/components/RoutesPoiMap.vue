<script setup>
import { computed, onMounted, ref } from 'vue'
import LeafletMap from '@shared/components/LeafletMap.vue'
import * as routesApi from '../api.js'

const FALLBACK_CENTER = [52.9651, 36.0785] // Орёл

const KIND_META = {
  grave: { label: 'Захоронения', icon: 'flag', dot: 'bg-error' },
  monument: { label: 'Памятники', icon: 'account_balance', dot: 'bg-secondary' },
  battle: { label: 'Места боёв', icon: 'star', dot: 'bg-tertiary' },
  hospital: { label: 'Госпитали', icon: 'medical_services', dot: 'bg-primary' },
  trench: { label: 'Окопы', icon: 'sports_motorsports', dot: 'bg-outline' },
  airfield: { label: 'Аэродромы', icon: 'flight', dot: 'bg-outline' },
  other: { label: 'Другое', icon: 'push_pin', dot: 'bg-outline' },
}

// По умолчанию — то, к чему семья реально может сходить пешком или доехать:
// захоронения и памятники. Остальные слои включаются вручную.
const activeKinds = ref(new Set(['grave', 'monument']))
const points = ref([])
const status = ref('loading') // loading | ready | error
const selectedId = ref(null)

onMounted(async () => {
  try {
    points.value = await routesApi.listPoi()
    status.value = 'ready'
  } catch {
    status.value = 'error'
  }
})

function toggleKind(kind) {
  const next = new Set(activeKinds.value)
  if (next.has(kind)) next.delete(kind)
  else next.add(kind)
  activeKinds.value = next
  selectedId.value = null
}

const visiblePoints = computed(() => points.value.filter((p) => activeKinds.value.has(p.kind)))

const markers = computed(() =>
  visiblePoints.value.map((p) => ({
    id: p.id,
    lat: p.lat,
    lng: p.lon,
    title: p.title,
    subtitle: KIND_META[p.kind]?.label,
  })),
)

const selected = computed(() => points.value.find((p) => p.id === selectedId.value) ?? null)

const kindsPresent = computed(() => {
  const present = new Set(points.value.map((p) => p.kind))
  return Object.keys(KIND_META).filter((k) => present.has(k))
})
</script>

<template>
  <section class="bg-surface-container-lowest rounded-lg shadow-sm overflow-hidden">
    <div class="p-5 pb-4 flex flex-col gap-3">
      <div class="flex items-start justify-between gap-3 flex-wrap">
        <div class="flex flex-col">
          <h2 class="font-headline-sm text-headline-sm text-on-surface">Куда можно сходить</h2>
          <p class="font-body-sm text-body-sm text-on-surface-variant">
            Слой «ВОВ»: захоронения и памятники рядом — данные из map_service
          </p>
        </div>
        <span v-if="status === 'ready'" class="font-label-sm text-label-sm text-on-surface-variant">
          {{ visiblePoints.length }} точек на карте
        </span>
      </div>

      <div v-if="kindsPresent.length" class="flex flex-wrap gap-2">
        <button
          v-for="kind in kindsPresent"
          :key="kind"
          type="button"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-full font-label-sm text-label-sm font-bold transition-all"
          :class="
            activeKinds.has(kind)
              ? 'bg-secondary text-on-secondary'
              : 'bg-surface-container-low text-on-surface-variant hover:bg-surface-container'
          "
          @click="toggleKind(kind)"
        >
          <span class="material-symbols-outlined text-[16px]">{{ KIND_META[kind].icon }}</span>
          {{ KIND_META[kind].label }}
        </button>
      </div>
    </div>

    <div class="relative h-96">
      <div v-if="status === 'loading'" class="absolute inset-0 flex items-center justify-center bg-surface-container">
        <span class="font-label-md text-label-md text-on-surface-variant flex items-center gap-2">
          <span class="material-symbols-outlined animate-spin text-[18px]">sync</span>
          Загружаем точки карты...
        </span>
      </div>
      <div v-else-if="status === 'error'" class="absolute inset-0 flex items-center justify-center bg-surface-container p-4 text-center">
        <span class="font-label-md text-label-md text-on-surface-variant">
          Не удалось загрузить слой «ВОВ» — map_service недоступен
        </span>
      </div>
      <template v-else>
        <LeafletMap :center="FALLBACK_CENTER" :zoom="9" :markers="markers" @marker-click="selectedId = $event" />
        <p v-if="!visiblePoints.length" class="absolute inset-x-0 top-3 flex justify-center pointer-events-none">
          <span class="px-3 py-1.5 rounded-full bg-surface-container-lowest/90 backdrop-blur font-label-sm text-label-sm text-on-surface-variant">
            Включите хотя бы один слой выше
          </span>
        </p>
      </template>
    </div>

    <div v-if="selected" class="p-5 border-t border-surface-container-high flex items-start gap-3">
      <div class="w-9 h-9 rounded-full bg-secondary-container text-on-secondary-container flex items-center justify-center shrink-0">
        <span class="material-symbols-outlined text-[18px]">{{ KIND_META[selected.kind]?.icon ?? 'push_pin' }}</span>
      </div>
      <div class="flex flex-col gap-1 min-w-0">
        <span class="font-label-lg text-label-lg text-on-surface font-bold">{{ selected.title }}</span>
        <span v-if="selected.description" class="font-body-sm text-body-sm text-on-surface-variant">{{ selected.description }}</span>
        <span v-if="selected.date_text" class="font-label-sm text-label-sm text-secondary font-bold">{{ selected.date_text }}</span>
        <span v-if="selected.source" class="font-label-sm text-label-sm text-on-surface-variant">Источник: {{ selected.source }}</span>
      </div>
    </div>
  </section>
</template>
