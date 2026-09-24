<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { useAsync } from '@/core/async'
import { errorText } from '@/core/format'
import { geolocationProblem, useGeolocation, type GeoMarker } from '@/core/geo'
import { listPoi } from '@/core/services/map'
import { useSessionStore } from '@/core/session'
import AccountRequired from '@/ui/AccountRequired.vue'
import GeoMap from '@/ui/geo/GeoMap.vue'
import MsIcon from '@/ui/MsIcon.vue'

import { createExcursion, isGuideRole } from './data'

type PlaceMode = 'here' | 'memorial'

interface Point {
  lat: number
  lon: number
  poiId: string | null
}

const router = useRouter()
const session = useSessionStore()
const { position, status: geoStatus, start: startLocating } = useGeolocation()

const isGuide = computed(() => session.hasAccount && isGuideRole(session.user?.role))

const title = ref('')
const description = ref('')
const placeName = ref('')
const placeMode = ref<PlaceMode>('memorial')
const memorialId = ref('')
const point = ref<Point | null>(null)
const startsAt = ref(defaultStart())
const capacity = ref(15)

const saving = ref(false)
const formError = ref<string | null>(null)

/** Места слоя «ВОВ» — экскурсию удобно ставить у памятника. Сервис не ответил — демо-набор. */
const places = useAsync(async () => (await listPoi()).data)

/** Ближайший полный час через час: экскурсию редко заводят «на сейчас». */
function defaultStart(): string {
  const date = new Date(Date.now() + 60 * 60 * 1000)
  date.setMinutes(0, 0, 0)
  const pad = (value: number): string => String(value).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

/** Место сбора — там, где стоит краевед: удобно, если экскурсию заводят прямо на месте. */
function useCurrentPosition(): void {
  placeMode.value = 'here'
  memorialId.value = ''
  if (position.value) point.value = { lat: position.value.lat, lon: position.value.lon, poiId: null }
  else startLocating()
}

watch(position, (fix) => {
  if (fix && placeMode.value === 'here') point.value = { lat: fix.lat, lon: fix.lon, poiId: null }
})

watch(memorialId, (id) => {
  const poi = places.data.value?.find((item) => item.id === id)
  if (!poi) return
  placeMode.value = 'memorial'
  point.value = { lat: poi.lat, lon: poi.lon, poiId: poi.id }
  placeName.value = poi.title
})

const markers = computed<GeoMarker[]>(() =>
  point.value
    ? [{ id: 'point', lat: point.value.lat, lon: point.value.lon, label: placeName.value || 'Место сбора', icon: 'groups', tone: 'primary' }]
    : [],
)

const geoProblem = computed(() => (placeMode.value === 'here' ? geolocationProblem(geoStatus.value) : null))

const canSubmit = computed(
  () => title.value.trim().length > 0 && point.value !== null && startsAt.value !== '' && capacity.value >= 1,
)

async function submit(): Promise<void> {
  if (!canSubmit.value || saving.value || !point.value) return
  saving.value = true
  formError.value = null
  try {
    const created = await createExcursion({
      title: title.value.trim(),
      description: description.value.trim(),
      place_name: placeName.value.trim(),
      lat: point.value.lat,
      lon: point.value.lon,
      poi_id: point.value.poiId,
      // datetime-local — время телефона без пояса; сервису отдаём UTC.
      starts_at: new Date(startsAt.value).toISOString(),
      capacity: Math.round(capacity.value),
    })
    await router.replace({ name: 'excursion', params: { excursionId: created.id } })
  } catch (reason) {
    formError.value = errorText(reason)
  } finally {
    saving.value = false
  }
}

const inputClass =
  'w-full rounded-DEFAULT bg-surface-container-low px-4 py-3 font-body-md text-body-md text-on-surface outline-none placeholder:text-outline focus:ring-2 focus:ring-primary'
</script>

<template>
  <div class="flex w-full flex-col gap-space-md px-margin pb-space-xl pt-space-sm">
    <AccountRequired v-if="!session.hasAccount" text="Создавать экскурсии можно только с аккаунтом краеведа." />

    <div v-else-if="!isGuide" class="flex items-start gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
      <MsIcon name="info" :size="20" class="mt-0.5 shrink-0 text-secondary" />
      <p class="font-body-sm text-body-sm text-on-surface-variant">
        Создавать экскурсии могут краеведы и наставники. Зарегистрируйтесь с отметкой «Я краевед» или попросите
        модератора сменить роль.
      </p>
    </div>

    <form v-else class="flex flex-col gap-space-md" @submit.prevent="submit">
      <label class="flex flex-col gap-1">
        <span class="font-label-md text-label-md text-on-surface">Название</span>
        <input v-model="title" type="text" maxlength="255" required placeholder="Тропа памяти: площадь Мира" :class="inputClass" />
      </label>

      <label class="flex flex-col gap-1">
        <span class="font-label-md text-label-md text-on-surface">О чём экскурсия</span>
        <textarea v-model="description" rows="3" placeholder="Что увидим, сколько идти, что взять с собой" :class="inputClass" />
      </label>

      <fieldset class="flex flex-col gap-space-sm">
        <legend class="mb-1 font-label-md text-label-md text-on-surface">Место сбора группы</legend>

        <label class="flex flex-col gap-1">
          <span class="font-label-sm text-label-sm text-on-surface-variant">У памятника со слоя «ВОВ»</span>
          <select v-model="memorialId" :class="inputClass" :disabled="places.loading.value">
            <option value="" disabled>{{ places.loading.value ? 'Загружаем места…' : 'Выберите место' }}</option>
            <option v-for="poi in places.data.value ?? []" :key="poi.id" :value="poi.id">{{ poi.title }}</option>
          </select>
        </label>

        <button
          type="button"
          class="flex items-center justify-center gap-1.5 rounded-full py-2.5 font-label-md text-label-md"
          :class="placeMode === 'here' ? 'bg-secondary text-on-secondary' : 'bg-secondary-container text-on-secondary-container'"
          @click="useCurrentPosition"
        >
          <MsIcon :name="geoStatus === 'locating' ? 'progress_activity' : 'my_location'" :size="18" :class="{ 'animate-spin': geoStatus === 'locating' }" />
          Там, где я сейчас
        </button>
        <p v-if="geoProblem" class="font-body-sm text-body-sm text-error" role="alert">{{ geoProblem }}</p>

        <GeoMap v-if="point" :markers="markers" selected="point" class="h-40 w-full rounded-2xl shadow-document" />

        <label class="flex flex-col gap-1">
          <span class="font-label-sm text-label-sm text-on-surface-variant">Как найти место</span>
          <input v-model="placeName" type="text" maxlength="255" placeholder="У Вечного огня, площадь Мира" :class="inputClass" />
        </label>
      </fieldset>

      <div class="grid grid-cols-[1fr_7rem] gap-space-sm">
        <label class="flex min-w-0 flex-col gap-1">
          <span class="font-label-md text-label-md text-on-surface">Начало</span>
          <input v-model="startsAt" type="datetime-local" required :class="inputClass" />
        </label>
        <label class="flex flex-col gap-1">
          <span class="font-label-md text-label-md text-on-surface">Мест</span>
          <input v-model.number="capacity" type="number" min="1" max="500" required :class="inputClass" />
        </label>
      </div>

      <p v-if="formError" class="rounded-DEFAULT bg-error-container px-3 py-2 font-body-sm text-body-sm text-on-error-container" role="alert">
        {{ formError }}
      </p>

      <button
        type="submit"
        class="flex w-full items-center justify-center gap-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-60"
        :disabled="!canSubmit || saving"
      >
        <MsIcon :name="saving ? 'progress_activity' : 'event_available'" :size="20" :class="{ 'animate-spin': saving }" />
        Опубликовать экскурсию
      </button>
      <p v-if="!point" class="text-center font-body-sm text-body-sm text-outline">Выберите место сбора — без него не опубликовать.</p>
    </form>
  </div>
</template>
