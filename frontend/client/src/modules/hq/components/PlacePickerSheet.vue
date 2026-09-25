<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'

import { OREL_CENTER, geolocationProblem, useGeolocation, type GeoMarker, type LatLon } from '@/core/geo'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import GeoMap from '@/ui/geo/GeoMap.vue'
import FormInput from '@/ui/form/FormInput.vue'

/**
 * Точка штаба отряда: поиск по адресу, «по моему местоположению» или тап по
 * карте — три способа поставить одну и ту же точку.
 *
 * Поиск — публичный Nominatim (OpenStreetMap), без ключа, как уже сделано с
 * OSRM в `core/geo/routing.ts`. У него жёсткий лимит — один запрос в секунду,
 * поэтому задержка ввода 600мс и отмена предыдущего запроса обязательны.
 */
const props = defineProps<{ point: LatLon | null }>()
const emit = defineEmits<{ close: []; picked: [point: LatLon] }>()

const point = ref<LatLon | null>(props.point)

const markers = ref<GeoMarker[]>([])
watch(
  point,
  (value) => {
    markers.value = value ? [{ id: 'штаб', lat: value.lat, lon: value.lon, label: 'Штаб отряда', icon: 'flag', tone: 'secondary' }] : []
  },
  { immediate: true },
)

function pick(next: LatLon): void {
  point.value = next
}

// --- геолокация «по моему местоположению» ---

const { position, status, start } = useGeolocation()
watch(position, (value) => {
  if (value) point.value = { lat: value.lat, lon: value.lon }
})

// --- поиск адреса (Nominatim) ---

interface SearchResult {
  lat: string
  lon: string
  display_name: string
}

const query = ref('')
const results = ref<SearchResult[]>([])
const searching = ref(false)
const searchError = ref<string | null>(null)
let searchTimer: ReturnType<typeof setTimeout> | undefined
let controller: AbortController | null = null

async function runSearch(text: string): Promise<void> {
  controller?.abort()
  if (!text.trim()) {
    results.value = []
    searchError.value = null
    return
  }
  controller = new AbortController()
  searching.value = true
  searchError.value = null
  try {
    const url = `https://nominatim.openstreetmap.org/search?format=jsonv2&countrycodes=ru&limit=5&q=${encodeURIComponent(text)}`
    const response = await fetch(url, { signal: controller.signal, headers: { Accept: 'application/json' } })
    if (!response.ok) throw new Error(`nominatim ${response.status}`)
    results.value = (await response.json()) as SearchResult[]
    if (!results.value.length) searchError.value = 'Ничего не нашлось — поставьте точку на карте вручную'
  } catch (reason) {
    if ((reason as { name?: string }).name === 'AbortError') return
    results.value = []
    searchError.value = 'Сервис поиска не ответил — поставьте точку на карте вручную'
  } finally {
    searching.value = false
  }
}

watch(query, (text) => {
  clearTimeout(searchTimer)
  // Лимит Nominatim — один запрос в секунду; 600мс с отменой предыдущего его не пробьют.
  searchTimer = setTimeout(() => void runSearch(text), 600)
})

function chooseResult(result: SearchResult): void {
  point.value = { lat: Number(result.lat), lon: Number(result.lon) }
  results.value = []
  query.value = result.display_name
}

onBeforeUnmount(() => {
  clearTimeout(searchTimer)
  controller?.abort()
})

function confirm(): void {
  if (point.value) emit('picked', point.value)
}
</script>

<template>
  <SheetDialog title="Где штаб отряда" subtitle="Точка попадёт на карту потребностей — по ней, а не по названию района" @close="emit('close')">
    <div class="flex flex-col gap-space-md">
      <FormInput v-model="query" label="Поиск по адресу" icon="search" placeholder="Улица, город" />
      <ul v-if="results.length" class="flex flex-col gap-1 rounded-2xl bg-surface-container-low p-1">
        <li v-for="result in results" :key="`${result.lat},${result.lon}`">
          <button
            type="button"
            class="flex w-full items-start gap-space-xs rounded-xl px-space-sm py-2 text-left font-body-sm text-body-sm text-on-surface hover:bg-surface-container-high"
            @click="chooseResult(result)"
          >
            <MsIcon name="location_on" :size="18" class="mt-0.5 shrink-0 text-on-surface-variant" />
            {{ result.display_name }}
          </button>
        </li>
      </ul>
      <InlineNotice v-else-if="searchError" tone="info">{{ searchError }}</InlineNotice>

      <button
        type="button"
        class="inline-flex items-center gap-space-xs self-start rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95 disabled:opacity-60"
        :disabled="status === 'locating'"
        @click="start"
      >
        <MsIcon :name="status === 'locating' ? 'progress_activity' : 'my_location'" :size="18" :class="{ 'animate-spin': status === 'locating' }" />
        Поставить по моему местоположению
      </button>
      <InlineNotice v-if="geolocationProblem(status)" tone="error">{{ geolocationProblem(status) }}</InlineNotice>

      <Transition appear name="map-in">
        <GeoMap
          :markers="markers"
          :center="point ?? OREL_CENTER"
          class="h-64 w-full overflow-hidden rounded-2xl"
          label="Тап по карте ставит точку"
          @pick="pick"
        />
      </Transition>

      <button
        type="button"
        class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70 short:py-2.5"
        :disabled="!point"
        @click="confirm"
      >
        <MsIcon name="check" :size="18" />
        <span>Использовать эту точку</span>
      </button>
    </div>
  </SheetDialog>
</template>

<style scoped>
/* Карта — не мгновенно, а проявляется: заметнее на первом открытии экрана, чем резкий скачок плиток. */
.map-in-enter-active {
  transition:
    opacity 320ms ease-out,
    transform 320ms cubic-bezier(0.22, 1, 0.36, 1);
}
.map-in-enter-from {
  opacity: 0;
  transform: scale(0.97);
}

@media (prefers-reduced-motion: reduce) {
  .map-in-enter-active {
    transition: opacity 150ms linear;
  }
  .map-in-enter-from {
    transform: none;
  }
}
</style>
