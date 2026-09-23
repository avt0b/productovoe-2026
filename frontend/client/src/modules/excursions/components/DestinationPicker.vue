<script setup lang="ts">
import { computed, ref } from 'vue'

import { useAsync } from '@/core/async'
import { distanceKm, formatDistance, type LatLon } from '@/core/geo'
import { listPoi, type Poi } from '@/core/services/map'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'

import type { WalkTarget } from '../data'

/**
 * Куда вести группу: памятные места слоя «ВОВ», ближние — первыми.
 *
 * Список, а не тап по карте: краевед стоит перед группой с телефоном в руке,
 * и попасть пальцем в памятник на карте сложнее, чем выбрать его по названию.
 */
const props = defineProps<{
  /** Откуда считать расстояние: где стоит краевед или место сбора. */
  from: LatLon
  /** Текущая цель — чтобы отметить её в списке. */
  currentPoiId?: string | null
  busy?: boolean
}>()

const emit = defineEmits<{ close: []; pick: [target: WalkTarget] }>()

/** Сколько мест показывать: дальше — уже не прогулка, а поездка. */
const LIMIT = 15

const query = ref('')
const places = useAsync(() => listPoi())

const nearest = computed(() => {
  const needle = query.value.trim().toLowerCase()
  return (places.data.value?.data ?? [])
    .filter((poi) => !needle || poi.title.toLowerCase().includes(needle))
    .map((poi) => ({ poi, km: distanceKm(props.from, poi) }))
    .sort((a, b) => a.km - b.km)
    .slice(0, LIMIT)
})

function choose(poi: Poi): void {
  if (props.busy) return
  emit('pick', { lat: poi.lat, lon: poi.lon, name: poi.title, poi_id: poi.id })
}
</script>

<template>
  <SheetDialog title="Куда ведём группу" subtitle="У всех на карте появится маршрут к этому месту" @close="emit('close')">
    <div class="flex flex-col gap-space-sm">
      <label class="flex items-center gap-space-xs rounded-full bg-surface-container px-space-md py-space-xs">
        <MsIcon name="search" :size="18" class="text-on-surface-variant" />
        <input
          v-model="query"
          type="search"
          placeholder="Памятник, мемориал, место боя"
          class="w-full bg-transparent font-body-md text-body-md text-on-surface outline-none placeholder:text-on-surface-variant"
        />
      </label>

      <p v-if="places.loading.value" class="py-space-md text-center font-body-sm text-body-sm text-on-surface-variant">
        Ищу места рядом…
      </p>
      <p v-else-if="places.error.value" class="py-space-md text-center font-body-sm text-body-sm text-error">
        {{ places.error.value }}
      </p>
      <p v-else-if="nearest.length === 0" class="py-space-md text-center font-body-sm text-body-sm text-on-surface-variant">
        Ничего не нашлось
      </p>

      <ul v-else class="-mx-space-xs flex max-h-[55vh] flex-col overflow-y-auto">
        <li v-for="{ poi, km } in nearest" :key="poi.id">
          <button
            type="button"
            class="flex w-full items-center gap-space-sm rounded-lg px-space-xs py-space-sm text-left transition-colors hover:bg-surface-container active:bg-surface-container-high disabled:opacity-60"
            :disabled="busy"
            @click="choose(poi)"
          >
            <span
              class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full"
              :class="poi.id === currentPoiId ? 'bg-primary text-on-primary' : 'bg-surface-container-high text-primary'"
            >
              <MsIcon :name="poi.id === currentPoiId ? 'flag' : 'account_balance'" :size="20" />
            </span>
            <span class="flex min-w-0 flex-1 flex-col">
              <span class="truncate font-label-lg text-label-lg text-on-surface">{{ poi.title }}</span>
              <span class="font-body-sm text-body-sm text-on-surface-variant">
                {{ poi.id === currentPoiId ? 'Идём сюда сейчас' : formatDistance(km) }}
              </span>
            </span>
            <MsIcon name="chevron_right" :size="20" class="text-on-surface-variant" />
          </button>
        </li>
      </ul>
    </div>
  </SheetDialog>
</template>
