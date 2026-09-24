<script setup lang="ts">
import { computed, ref } from 'vue'

import { useAsync } from '@/core/async'
import { distanceKm, formatDistance, type LatLon } from '@/core/geo'
import { listPoi, type Poi } from '@/core/services/map'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'

import { sameSpot, type WalkTarget } from '../data'

/**
 * Выбор памятного места: куда вести группу или какую точку добавить в маршрут.
 * Места слоя «ВОВ» — ближние первыми; точки маршрута экскурсии, если он есть,
 * — отдельно сверху и по порядку.
 *
 * Список, а не тап по карте: краевед стоит перед группой с телефоном в руке,
 * и попасть пальцем в памятник на карте сложнее, чем выбрать его по названию.
 */
const props = withDefaults(
  defineProps<{
    /** Откуда считать расстояние: где стоит краевед или место сбора. */
    from: LatLon
    /** Текущая цель — чтобы отметить её в списке. */
    current?: LatLon | null
    /** Маршрут экскурсии — показывается первым. */
    stops?: WalkTarget[]
    title?: string
    subtitle?: string
    busy?: boolean
  }>(),
  {
    current: null,
    stops: () => [],
    title: 'Куда ведём группу',
    subtitle: 'У всех на карте появится маршрут к этому месту',
    busy: false,
  },
)

const emit = defineEmits<{ close: []; pick: [target: WalkTarget] }>()

/** Сколько мест показывать: дальше — уже не прогулка, а поездка. */
const LIMIT = 15

const query = ref('')
const places = useAsync(() => listPoi())

const needle = computed(() => query.value.trim().toLowerCase())
const routeStops = computed(() => props.stops.filter((stop) => !needle.value || stop.name.toLowerCase().includes(needle.value)))

const nearest = computed(() =>
  (places.data.value?.data ?? [])
    .filter((poi) => !needle.value || poi.title.toLowerCase().includes(needle.value))
    .map((poi) => ({ poi, km: distanceKm(props.from, poi) }))
    .sort((a, b) => a.km - b.km)
    .slice(0, LIMIT),
)

function isCurrent(point: LatLon): boolean {
  return props.current !== null && sameSpot(props.current, point)
}

function choose(target: WalkTarget): void {
  if (!props.busy) emit('pick', target)
}

function fromPoi(poi: Poi): WalkTarget {
  return { lat: poi.lat, lon: poi.lon, name: poi.title, poi_id: poi.id }
}
</script>

<template>
  <SheetDialog :title="title" :subtitle="subtitle" @close="emit('close')">
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

      <div class="-mx-space-xs flex max-h-[55vh] flex-col overflow-y-auto">
        <template v-if="routeStops.length">
          <p class="px-space-xs pb-1 pt-space-xs font-archival text-archival uppercase text-on-surface-variant">По маршруту экскурсии</p>
          <ul class="flex flex-col">
            <li v-for="(stop, index) in routeStops" :key="`${stop.lat},${stop.lon},${index}`">
              <button
                type="button"
                class="flex w-full items-center gap-space-sm rounded-2xl px-space-xs py-space-sm text-left transition-colors hover:bg-surface-container active:bg-surface-container-high disabled:opacity-60"
                :disabled="busy"
                @click="choose(stop)"
              >
                <span
                  class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full font-label-lg text-label-lg"
                  :class="isCurrent(stop) ? 'bg-primary text-on-primary' : 'bg-secondary-container text-on-secondary-container'"
                >
                  {{ stops.indexOf(stop) + 1 }}
                </span>
                <span class="flex min-w-0 flex-1 flex-col">
                  <span class="truncate font-label-lg text-label-lg text-on-surface">{{ stop.name }}</span>
                  <span class="font-body-sm text-body-sm text-on-surface-variant">
                    {{ isCurrent(stop) ? 'Идём сюда сейчас' : formatDistance(distanceKm(from, stop)) }}
                  </span>
                </span>
                <MsIcon name="chevron_right" :size="20" class="text-on-surface-variant" />
              </button>
            </li>
          </ul>
          <p class="px-space-xs pb-1 pt-space-sm font-archival text-archival uppercase text-on-surface-variant">Другие места рядом</p>
        </template>

        <p v-if="places.loading.value" class="py-space-md text-center font-body-sm text-body-sm text-on-surface-variant">
          Ищу места рядом…
        </p>
        <p v-else-if="places.error.value" class="py-space-md text-center font-body-sm text-body-sm text-error">
          {{ places.error.value }}
        </p>
        <p v-else-if="nearest.length === 0" class="py-space-md text-center font-body-sm text-body-sm text-on-surface-variant">
          Ничего не нашлось
        </p>

        <ul v-else class="flex flex-col">
          <li v-for="{ poi, km } in nearest" :key="poi.id">
            <button
              type="button"
              class="flex w-full items-center gap-space-sm rounded-2xl px-space-xs py-space-sm text-left transition-colors hover:bg-surface-container active:bg-surface-container-high disabled:opacity-60"
              :disabled="busy"
              @click="choose(fromPoi(poi))"
            >
              <span
                class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full"
                :class="isCurrent(poi) ? 'bg-primary text-on-primary' : 'bg-surface-container-high text-primary'"
              >
                <MsIcon :name="isCurrent(poi) ? 'flag' : 'account_balance'" :size="20" />
              </span>
              <span class="flex min-w-0 flex-1 flex-col">
                <span class="truncate font-label-lg text-label-lg text-on-surface">{{ poi.title }}</span>
                <span class="font-body-sm text-body-sm text-on-surface-variant">
                  {{ isCurrent(poi) ? 'Идём сюда сейчас' : formatDistance(km) }}
                </span>
              </span>
              <MsIcon name="chevron_right" :size="20" class="text-on-surface-variant" />
            </button>
          </li>
        </ul>
      </div>
    </div>
  </SheetDialog>
</template>
