<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { errorText } from '@/core/format'
import { OREL_CENTER, formatCoordinates, useGeolocation, type GeoMarker, type LatLon } from '@/core/geo'
import { createPoi, type PoiKind } from '@/core/services/map'
import GeoMap from '@/ui/geo/GeoMap.vue'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import FormInput from '@/ui/form/FormInput.vue'
import FormSelect from '@/ui/form/FormSelect.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

import { PLACE_KINDS } from '../data'

/**
 * Новое место на слое «ВОВ» — то, что ТЗ называет «дополнять данные»: памятник,
 * захоронение, окоп, которых нет на карте. Место видно всем сразу: слой ведут
 * краеведы, поисковики и наставники, и отвечают за него они же.
 */
const emit = defineEmits<{ close: []; created: [] }>()

const KIND_ORDER: readonly PoiKind[] = ['monument', 'grave', 'battle', 'trench', 'airfield', 'hospital', 'other']
const kindOptions = KIND_ORDER.map((kind) => ({ value: kind, title: PLACE_KINDS[kind].title }))

const kind = ref<PoiKind>('monument')
const title = ref('')
const description = ref('')
const dateText = ref('')
const source = ref('')
const point = ref<LatLon>(OREL_CENTER)
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
  if (!fix || !takeMyPosition) return
  takeMyPosition = false
  setPoint(fix)
})

function setPoint(next: LatLon): void {
  // Шесть знаков — около 10 см: точнее GPS всё равно не даст.
  const round = (value: number): number => Math.round(value * 1e6) / 1e6
  point.value = { lat: round(next.lat), lon: round(next.lon) }
}

const markers = computed<GeoMarker[]>(() => [
  {
    id: 'new',
    lat: point.value.lat,
    lon: point.value.lon,
    label: title.value || 'Новое место',
    icon: PLACE_KINDS[kind.value].icon,
    tone: PLACE_KINDS[kind.value].tone,
  },
])

const missing = computed(() => {
  if (!title.value.trim()) return 'Назовите место'
  if (!source.value.trim()) return 'Укажите источник: по нему проверят сведения'
  return null
})

async function save(): Promise<void> {
  if (missing.value || saving.value) return
  saving.value = true
  error.value = null
  try {
    await createPoi({
      kind: kind.value,
      title: title.value.trim(),
      description: description.value.trim(),
      lat: point.value.lat,
      lon: point.value.lon,
      date_text: dateText.value.trim(),
      source: source.value.trim(),
    })
    emit('created')
    emit('close')
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <SheetDialog title="Новое место на карте" subtitle="Слой «ВОВ» — его видят все, кто открывает карту" @close="emit('close')">
    <form class="flex flex-col gap-space-md" @submit.prevent="save">
      <GeoMap
        selected="new"
        :markers="markers"
        :center="point"
        :user="position"
        :locating="geoStatus === 'locating'"
        label="Нажмите на карту, чтобы поставить метку"
        class="h-48 w-full rounded-2xl shadow-document short:h-40"
        @pick="setPoint"
        @locate="useMyPosition"
      />
      <div class="flex items-center justify-between gap-space-sm">
        <span class="min-w-0 font-body-sm text-body-sm text-on-surface-variant">{{ formatCoordinates(point) }}</span>
        <button
          type="button"
          class="flex shrink-0 items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
          @click="useMyPosition"
        >
          <MsIcon name="my_location" :size="18" />
          Я здесь
        </button>
      </div>

      <FormSelect v-model="kind" label="Что это за место" :options="kindOptions" icon="pin_drop" />
      <FormInput v-model="title" label="Название" icon="military_tech" :maxlength="255" placeholder="Памятник воинам-артиллеристам" required />
      <FormTextarea
        v-model="description"
        label="Что здесь было"
        :rows="3"
        :maxlength="4000"
        placeholder="Коротко: что за место, чем оно важно, что видно на месте"
      />
      <FormInput v-model="dateText" label="Когда" icon="event" :maxlength="120" placeholder="5 августа 1943" />
      <FormInput
        v-model="source"
        label="Источник"
        icon="menu_book"
        :maxlength="500"
        placeholder="Книга Памяти Орловской области, т. 5"
        hint="По нему другие краеведы проверят сведения"
        required
      />

      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>
      <p v-else-if="missing" class="text-center font-body-sm text-body-sm text-on-surface-variant">{{ missing }}</p>

      <button
        type="submit"
        class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70 short:py-2.5"
        :disabled="missing !== null || saving"
      >
        <MsIcon :name="saving ? 'progress_activity' : 'add_location_alt'" :size="18" :class="{ 'animate-spin': saving }" />
        <span>Добавить на карту</span>
      </button>
    </form>
  </SheetDialog>
</template>
