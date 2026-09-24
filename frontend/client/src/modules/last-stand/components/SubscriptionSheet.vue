<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { useAsync } from '@/core/async'
import { errorText } from '@/core/format'
import { geolocationProblem, useGeolocation, type GeoMarker, type LatLon } from '@/core/geo'
import GeoMap from '@/ui/geo/GeoMap.vue'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import StateBlock from '@/ui/StateBlock.vue'
import ToggleSwitch from '@/ui/ToggleSwitch.vue'

import { RADIUS_OPTIONS_KM, fetchSubscription, saveSubscription, type MapCircle, type SearchSubscription } from '../data'

/**
 * «Находки рядом» — подписка на район из кейса: когда поисковики отметят место
 * гибели в радиусе от «дома», придёт «в N км от вас обнаружено место гибели».
 *
 * Дом — не адрес, а точка, от которой считается радиус: можно поставить её на
 * деревню, где работает отряд, а не туда, где человек живёт.
 */
const emit = defineEmits<{ close: []; saved: [subscription: SearchSubscription] }>()

const current = useAsync(fetchSubscription)

const subscribed = ref(true)
const radiusKm = ref<number>(RADIUS_OPTIONS_KM[1])
const home = ref<LatLon | null>(null)
const saving = ref(false)
const error = ref<string | null>(null)

// Подтянули сохранённое — показываем его, а не значения по умолчанию.
watch(current.data, (saved) => {
  if (!saved) return
  // Сохранённой подписки ещё нет — включаем её сразу: человек за этим и пришёл.
  subscribed.value = saved.subscribed || saved.home === null
  radiusKm.value = (RADIUS_OPTIONS_KM as readonly number[]).includes(saved.radiusKm) ? saved.radiusKm : RADIUS_OPTIONS_KM[1]
  home.value = saved.home
})

const { position, status: geoStatus, start: startLocating } = useGeolocation()
let takeMyPosition = false

function useMyPosition(): void {
  takeMyPosition = true
  if (position.value) setHome(position.value)
  else startLocating()
}

watch(position, (fix) => {
  if (fix && takeMyPosition) {
    takeMyPosition = false
    setHome(fix)
  }
})

function setHome(point: LatLon): void {
  // Три знака — около ста метров: для «в 5 км от вас» точнее не нужно, а
  // точный адрес дома в профиле хранить незачем.
  const round = (value: number): number => Math.round(value * 1e3) / 1e3
  home.value = { lat: round(point.lat), lon: round(point.lon) }
}

const markers = computed<GeoMarker[]>(() =>
  home.value ? [{ id: 'home', ...home.value, label: 'Центр района', icon: 'home_pin', tone: 'secondary' }] : [],
)

const circles = computed<MapCircle[]>(() =>
  home.value ? [{ id: 'radius', ...home.value, radiusMeters: radiusKm.value * 1000, tone: 'secondary' }] : [],
)

const radiusIndex = computed(() => (RADIUS_OPTIONS_KM as readonly number[]).indexOf(radiusKm.value))
const geoProblem = computed(() => geolocationProblem(geoStatus.value))
/** Выключить подписку можно и без точки; включить — только указав, откуда считать. */
const valid = computed(() => !subscribed.value || home.value !== null)

async function save(): Promise<void> {
  if (!valid.value || saving.value) return
  saving.value = true
  error.value = null
  try {
    const saved = await saveSubscription({ subscribed: subscribed.value, radiusKm: radiusKm.value, home: home.value })
    emit('saved', saved)
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <SheetDialog title="Находки рядом" subtitle="Сообщим, когда поисковики отметят место гибели в вашем районе" @close="emit('close')">
    <StateBlock v-if="current.loading.value || current.error.value" :loading="current.loading.value" :error="current.error.value" @retry="current.retry" />

    <form v-else class="flex flex-col gap-space-lg" @submit.prevent="save">
      <label class="flex items-center justify-between gap-space-md rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
        <span class="flex min-w-0 flex-col">
          <span class="font-label-lg text-label-lg text-on-surface">Сообщать о новых местах</span>
          <span class="font-body-sm text-body-sm text-on-surface-variant">«В 5 км от вас обнаружено место гибели бойца»</span>
        </span>
        <ToggleSwitch v-model="subscribed" label="Сообщать о новых местах гибели рядом" />
      </label>

      <!-- Район схлопывается, когда подписка выключена: настраивать его незачем. -->
      <div
        class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
        :class="subscribed ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
        :inert="!subscribed"
      >
        <div class="flex flex-col gap-space-sm overflow-hidden">
          <span class="font-archival text-archival uppercase text-on-surface-variant">Радиус</span>
          <div class="relative grid grid-cols-3 rounded-xl bg-surface-container p-1 text-center" role="radiogroup" aria-label="Радиус района">
            <span
              class="absolute inset-y-1 left-1 w-[calc((100%-8px)/3)] rounded-lg bg-surface-container-lowest shadow-float transition-transform duration-300 ease-out"
              :style="{ transform: `translateX(${Math.max(radiusIndex, 0) * 100}%)` }"
              aria-hidden="true"
            />
            <button
              v-for="option in RADIUS_OPTIONS_KM"
              :key="option"
              type="button"
              role="radio"
              :aria-checked="radiusKm === option"
              class="relative z-10 rounded-lg py-2 font-label-lg text-label-lg transition-colors duration-200"
              :class="radiusKm === option ? 'text-on-surface' : 'text-on-surface-variant'"
              @click="radiusKm = option"
            >
              {{ option }} км
            </button>
          </div>

          <span class="mt-space-xs font-archival text-archival uppercase text-on-surface-variant">Откуда считать</span>
          <GeoMap
            :selected="home ? 'home' : null"
            :markers="markers"
            :circles="circles"
            :user="position"
            :locating="geoStatus === 'locating'"
            label="Нажмите на карту, чтобы выбрать центр района"
            class="h-56 w-full rounded-2xl shadow-document short:h-44"
            @pick="setHome"
            @locate="useMyPosition"
          />
          <button
            type="button"
            class="flex items-center justify-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
            @click="useMyPosition"
          >
            <MsIcon
              :name="geoStatus === 'locating' ? 'progress_activity' : 'my_location'"
              :size="18"
              :class="{ 'animate-spin': geoStatus === 'locating' }"
            />
            Считать от того места, где я сейчас
          </button>
          <InlineNotice v-if="geoProblem" tone="error" icon="location_off">{{ geoProblem }}</InlineNotice>
        </div>
      </div>

      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>
      <p v-else-if="!valid" class="text-center font-body-sm text-body-sm text-on-surface-variant">
        Выберите на карте, от какой точки считать радиус
      </p>

      <button
        type="submit"
        class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70 short:py-2.5"
        :disabled="!valid || saving"
      >
        <MsIcon :name="saving ? 'progress_activity' : 'notifications_active'" :size="18" :class="{ 'animate-spin': saving }" />
        <span>{{ subscribed ? 'Подписаться' : 'Отписаться' }}</span>
      </button>
    </form>
  </SheetDialog>
</template>
