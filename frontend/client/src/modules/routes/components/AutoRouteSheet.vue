<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { errorText } from '@/core/format'
import { OREL_CENTER, formatCoordinates, useGeolocation, type GeoMarker, type LatLon } from '@/core/geo'
import { autoGenerateRoute, type RouteDetail, type RouteMode } from '@/core/services/routes'
import GeoMap from '@/ui/geo/GeoMap.vue'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import FormInput from '@/ui/form/FormInput.vue'
import FormSelect from '@/ui/form/FormSelect.vue'

/**
 * Черновик по точкам слоя «ВОВ» рядом — «автоматически строить квест-маршруты»
 * из ТЗ. Сервис расставляет точки на карте, а рассказ, детское задание и
 * AR-подсказку краевед дописывает сам: без них маршрут не опубликуется.
 */
const emit = defineEmits<{ close: []; created: [route: RouteDetail] }>()

const MODES: readonly { value: RouteMode; title: string }[] = [
  { value: 'family', title: 'Семейный: с заданиями для детей' },
  { value: 'general', title: 'Общий: для всех' },
]

const RADIUS: readonly { value: string; title: string }[] = [
  { value: '1', title: '1 км — пешком по кварталу' },
  { value: '3', title: '3 км — центр города' },
  { value: '10', title: '10 км — город и окраины' },
]

const title = ref('')
const city = ref('Орёл')
const mode = ref<RouteMode>('family')
const radius = ref('3')
const maxPoints = ref<number | null>(4)
const center = ref<LatLon>(OREL_CENTER)
const saving = ref(false)
const error = ref<string | null>(null)

const { position, status: geoStatus, start: startLocating } = useGeolocation()
let takeMyPosition = false

function useMyPosition(): void {
  takeMyPosition = true
  if (position.value) center.value = { lat: position.value.lat, lon: position.value.lon }
  else startLocating()
}

watch(position, (fix) => {
  if (!fix || !takeMyPosition) return
  takeMyPosition = false
  center.value = { lat: fix.lat, lon: fix.lon }
})

const markers = computed<GeoMarker[]>(() => [
  { id: 'center', lat: center.value.lat, lon: center.value.lon, label: 'Отсюда собираем маршрут', icon: 'explore', tone: 'primary' },
])

async function generate(): Promise<void> {
  if (saving.value) return
  saving.value = true
  error.value = null
  try {
    emit(
      'created',
      await autoGenerateRoute({
        lat: center.value.lat,
        lon: center.value.lon,
        radius_km: Number(radius.value),
        max_points: Math.min(20, Math.max(2, Math.round(maxPoints.value ?? 4))),
        title: title.value.trim() || `Маршрут по местам памяти: ${city.value.trim() || 'Орёл'}`,
        mode: mode.value,
        city: city.value.trim(),
      }),
    )
    emit('close')
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <SheetDialog title="Собрать черновик" subtitle="Возьмём точки слоя «ВОВ» вокруг выбранного места" @close="emit('close')">
    <form class="flex flex-col gap-space-md" @submit.prevent="generate">
      <GeoMap
        selected="center"
        :markers="markers"
        :center="center"
        :user="position"
        :locating="geoStatus === 'locating'"
        label="Нажмите на карту, чтобы сдвинуть центр"
        class="h-48 w-full rounded-2xl shadow-document short:h-40"
        @pick="center = $event"
        @locate="useMyPosition"
      />
      <div class="flex items-center justify-between gap-space-sm">
        <span class="min-w-0 font-body-sm text-body-sm text-on-surface-variant">{{ formatCoordinates(center) }}</span>
        <button
          type="button"
          class="flex shrink-0 items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
          @click="useMyPosition"
        >
          <MsIcon name="my_location" :size="18" />
          Я здесь
        </button>
      </div>

      <FormSelect v-model="radius" label="В каком радиусе искать" :options="RADIUS" icon="radar" />
      <FormInput
        v-model="maxPoints"
        label="Сколько точек"
        icon="flag"
        type="number"
        :min="2"
        :max="20"
        inputmode="numeric"
        hint="Столько мест сервис возьмёт, если найдёт их рядом"
      />
      <FormSelect v-model="mode" label="Для кого" :options="MODES" icon="family_restroom" />
      <FormInput v-model="title" label="Название" icon="route" :maxlength="255" placeholder="Можно оставить пустым — придумаем сами" />
      <FormInput v-model="city" label="Город или район" icon="home_pin" :maxlength="120" placeholder="Орёл" />

      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>
      <InlineNotice v-else tone="info">
        Получится черновик: точки на карте уже будут, а рассказ, детское задание и AR-подсказку допишете сами.
      </InlineNotice>

      <button
        type="submit"
        class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70 short:py-2.5"
        :disabled="saving"
      >
        <MsIcon :name="saving ? 'progress_activity' : 'auto_awesome'" :size="18" :class="{ 'animate-spin': saving }" />
        <span>Собрать черновик</span>
      </button>
    </form>
  </SheetDialog>
</template>
