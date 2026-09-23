<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { errorText } from '@/core/format'
import { formatCoordinates, geolocationProblem, useGeolocation, type GeoMarker, type LatLon } from '@/core/geo'
import GeoMap from '@/ui/geo/GeoMap.vue'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import FormInput from '@/ui/form/FormInput.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

import { createPoint } from '../data'

/**
 * Новое место гибели — сценарий кейса: командир отряда «Высота» вносит
 * координаты места гибели десантников 9-й бригады, найденные в экспедиции.
 * Место появляется со статусом «Обнаружено», подтверждает его модератор.
 */
const emit = defineEmits<{ close: []; created: [] }>()

const soldierName = ref('')
const unit = ref('')
const circumstances = ref('')
const dateText = ref('')
const source = ref('')
const point = ref<LatLon | null>(null)
const lat = ref<number | null>(null)
const lon = ref<number | null>(null)
const saving = ref(false)
const error = ref<string | null>(null)

const { position, status: geoStatus, start: startLocating } = useGeolocation()
let takeMyPosition = false

function useMyPosition(): void {
  takeMyPosition = true
  if (position.value) setPoint(position.value)
  else startLocating()
}

watch(position, (fix) => {
  if (fix && takeMyPosition) {
    takeMyPosition = false
    setPoint(fix)
  }
})

function setPoint(next: LatLon): void {
  // Шесть знаков — около 10 см: точнее GPS всё равно не даст.
  const round = (value: number): number => Math.round(value * 1e6) / 1e6
  point.value = { lat: round(next.lat), lon: round(next.lon) }
  lat.value = point.value.lat
  lon.value = point.value.lon
}

// Координаты ввели руками — ставим точку туда же.
watch([lat, lon], ([nextLat, nextLon]) => {
  if (nextLat === null || nextLon === null) return
  if (Math.abs(nextLat) > 90 || Math.abs(nextLon) > 180) return
  if (point.value?.lat === nextLat && point.value?.lon === nextLon) return
  point.value = { lat: nextLat, lon: nextLon }
})

const markers = computed<GeoMarker[]>(() =>
  point.value ? [{ id: 'new', ...point.value, label: soldierName.value || 'Новое место', icon: 'person_search', tone: 'primary' }] : [],
)
const geoProblem = computed(() => geolocationProblem(geoStatus.value))
const valid = computed(() => point.value !== null && (soldierName.value.trim() || circumstances.value.trim()))

async function submit(): Promise<void> {
  if (!valid.value || saving.value || !point.value) return
  saving.value = true
  error.value = null
  try {
    await createPoint({
      ...point.value,
      soldier_name: soldierName.value.trim(),
      unit: unit.value.trim(),
      circumstances: circumstances.value.trim(),
      date_text: dateText.value.trim(),
      source: source.value.trim(),
    })
    emit('created')
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <SheetDialog title="Отметить место гибели" subtitle="Появится со статусом «Обнаружено», проверит модератор" @close="emit('close')">
    <form class="flex flex-col gap-space-md" @submit.prevent="submit">
      <fieldset class="flex flex-col gap-space-sm">
        <legend class="mb-1 font-label-md text-label-md text-on-surface">Где</legend>
        <GeoMap
          :selected="point ? 'new' : null"
          :markers="markers"
          :user="position"
          :locating="geoStatus === 'locating'"
          label="Нажмите на карту, чтобы поставить точку"
          class="h-56 w-full rounded-lg shadow-sm"
          @pick="setPoint"
          @locate="useMyPosition"
        />
        <button
          type="button"
          class="flex items-center justify-center gap-1.5 rounded-full bg-secondary-container py-2.5 font-label-md text-label-md text-on-secondary-container"
          @click="useMyPosition"
        >
          <MsIcon :name="geoStatus === 'locating' ? 'progress_activity' : 'my_location'" :size="18" :class="{ 'animate-spin': geoStatus === 'locating' }" />
          Я на месте — взять мои координаты
        </button>
        <p v-if="geoProblem" class="font-body-sm text-body-sm text-error" role="alert">{{ geoProblem }}</p>
        <div class="grid grid-cols-2 gap-space-sm">
          <FormInput v-model="lat" label="Широта" type="number" inputmode="decimal" step="any" :min="-90" :max="90" />
          <FormInput v-model="lon" label="Долгота" type="number" inputmode="decimal" step="any" :min="-180" :max="180" />
        </div>
        <p v-if="point" class="font-body-sm text-body-sm text-outline">{{ formatCoordinates(point) }}</p>
      </fieldset>

      <FormInput v-model="soldierName" label="Кто погиб" :maxlength="255" placeholder="Три неизвестных десантника" hint="Если имя неизвестно — так и напишите" />
      <FormInput v-model="unit" label="Часть" :maxlength="255" placeholder="9-я воздушно-десантная бригада, 5-й ВДК" />
      <FormTextarea v-model="circumstances" label="Обстоятельства" :rows="3" placeholder="Что нашли, как привязано к местности" />
      <FormInput v-model="dateText" label="Когда" :maxlength="120" placeholder="Октябрь 1941" />
      <FormInput v-model="source" label="Источник" placeholder="Отчёт экспедиции, Книга Памяти, т. 4, рассказ жителей" />

      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>

      <button
        type="submit"
        class="flex w-full items-center justify-center gap-2 rounded-full bg-primary py-3.5 font-label-lg text-label-lg text-on-primary shadow-md active:scale-[0.99] disabled:opacity-60"
        :disabled="!valid || saving"
      >
        <MsIcon :name="saving ? 'progress_activity' : 'add_location_alt'" :size="20" :class="{ 'animate-spin': saving }" />
        Отметить место
      </button>
      <p v-if="!point" class="text-center font-body-sm text-body-sm text-outline">Поставьте точку на карте или возьмите свои координаты.</p>
    </form>
  </SheetDialog>
</template>
