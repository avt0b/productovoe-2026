<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { useAsync } from '@/core/async'
import { getMyProgress } from '@/core/services/routes'
import { useSessionStore } from '@/core/session'
import {
  distanceKm,
  formatDistance,
  geolocationProblem,
  useGeolocation,
  type GeoMarker,
  type GeoPath,
  type LatLon,
} from '@/core/geo'
import DemoDataBadge from '@/ui/DemoDataBadge.vue'
import GeoMap from '@/ui/geo/GeoMap.vue'
import MsIcon from '@/ui/MsIcon.vue'
import StateBlock from '@/ui/StateBlock.vue'

import FeaturedRouteCard from './components/FeaturedRouteCard.vue'
import PlaceCard from './components/PlaceCard.vue'
import RouteFilters from './components/RouteFilters.vue'
import RoutesSearchBar from './components/RoutesSearchBar.vue'
import { PLACE_KINDS, fetchRoutesOverview, type RouteStop } from './data'

const router = useRouter()
const session = useSessionStore()
const { data, loading, error, retry } = useAsync(fetchRoutesOverview)

/** Пройденные точки маршрута дня — только с аккаунтом и живыми данными: прогресс хранит `route_service`. */
const completedIds = ref<string[] | null>(null)
watch(
  data,
  async (overview) => {
    completedIds.value = null
    if (!overview?.route || overview.source !== 'live' || !session.hasAccount) return
    try {
      completedIds.value = (await getMyProgress(overview.route.id))?.completed_waypoint_ids ?? null
    } catch {
      // Прогресс — дополнение к карте: не загрузился — карта и маршрут всё равно на месте.
    }
  },
  { immediate: true },
)
const { position: userPosition, status: geoStatus, start: startLocating } = useGeolocation()

const query = ref('')
/** Выбранные виды мест. Пусто — на карте все. */
const activeKinds = ref<Set<string>>(new Set())
const selectedId = ref<string | null>(null)

const normalizedQuery = computed(() => query.value.trim().toLowerCase())

const visiblePlaces = computed(() =>
  (data.value?.places ?? []).filter(
    (place) =>
      (activeKinds.value.size === 0 || activeKinds.value.has(place.kind)) &&
      (!normalizedQuery.value || `${place.title} ${place.description}`.toLowerCase().includes(normalizedQuery.value)),
  ),
)

const stops = computed(() => data.value?.route?.stops ?? [])

/** Места, которые уже стоят на маршруте номерами, — вторую метку поверх не рисуем. */
const placesOnRoute = computed(() => new Set(stops.value.map((stop) => stop.poiId).filter(Boolean)))

const markers = computed<GeoMarker[]>(() => [
  ...visiblePlaces.value
    .filter((place) => !placesOnRoute.value.has(place.id))
    .map((place) => ({
      id: place.id,
      lat: place.lat,
      lon: place.lon,
      label: place.title,
      icon: PLACE_KINDS[place.kind].icon,
      tone: PLACE_KINDS[place.kind].tone,
    })),
  ...stops.value.map((stop) => ({
    id: stop.id,
    lat: stop.lat,
    lon: stop.lon,
    label: `${stop.step}. ${stop.title}`,
    icon: 'flag',
    tone: 'secondary' as const,
    badge: String(stop.step),
  })),
])

/** Маршрут дня пунктиром — «след» из кейса. */
const paths = computed<GeoPath[]>(() => {
  const route = data.value?.route
  return route ? [{ id: route.id, points: route.stops, tone: 'secondary', dashed: true }] : []
})

const selectedPlace = computed(() => data.value?.places.find((place) => place.id === selectedId.value) ?? null)
const selectedStop = computed(() => stops.value.find((stop) => stop.id === selectedId.value) ?? null)

// Как в макете: сначала подсвечено начало маршрута дня.
watch(data, (overview) => {
  if (overview?.route && selectedId.value === null) selectedId.value = overview.route.stops[0]?.id ?? null
})

// Выбранное место спрятали поиском или фильтром — закрываем его карточку.
watch(markers, (items) => {
  if (selectedId.value && !items.some((marker) => marker.id === selectedId.value)) selectedId.value = null
})

function distanceFromUser(target: LatLon | null): string | null {
  return target && userPosition.value ? formatDistance(distanceKm(userPosition.value, target)) : null
}

const geoProblem = computed(() => geolocationProblem(geoStatus.value))

/** Точка маршрута — отдельный модуль. Нет его — кнопки старта просто не ведут никуда. */
const canOpenPoint = computed(() => router.hasRoute('route-point'))

function openStop(stop: RouteStop): void {
  const route = data.value?.route
  if (!route || !canOpenPoint.value) return
  void router.push({ name: 'route-point', params: { pointId: stop.id }, query: { route: route.id } })
}
</script>

<template>
  <div class="relative flex w-full flex-col">
    <div class="z-30 flex flex-col gap-space-sm px-margin pb-space-sm pt-space-xs">
      <RoutesSearchBar v-model="query" />
      <RouteFilters v-if="data?.filters.length" v-model="activeKinds" :filters="data.filters" />
    </div>

    <div v-if="loading || error" class="px-margin">
      <StateBlock :loading="loading" :error="error" @retry="retry" />
    </div>

    <template v-else-if="data">
      <DemoDataBadge v-if="data.source === 'demo'" class="mx-margin mb-space-sm" />

      <GeoMap
        v-model:selected="selectedId"
        :markers="markers"
        :paths="paths"
        :user="userPosition"
        :locating="geoStatus === 'locating'"
        :label="data.route?.title"
        class="h-[420px] w-full"
        @locate="startLocating"
      />

      <div class="flex flex-col gap-space-sm px-margin pt-space-md">
        <p
          v-if="geoProblem"
          class="flex items-start gap-2 rounded-DEFAULT bg-surface-container-high px-3 py-2 font-body-sm text-body-sm text-on-surface-variant"
          role="status"
        >
          <MsIcon name="location_off" :size="18" class="mt-0.5 shrink-0" />
          {{ geoProblem }}
        </p>

        <p
          v-if="visiblePlaces.length === 0"
          class="flex items-start gap-2 rounded-DEFAULT bg-surface-container-high px-3 py-2 font-body-sm text-body-sm text-on-surface-variant"
          role="status"
        >
          <MsIcon name="filter_alt_off" :size="18" class="mt-0.5 shrink-0" />
          Под поиск и фильтры мест нет
        </p>

        <PlaceCard
          v-if="selectedPlace"
          :key="selectedPlace.id"
          :place="selectedPlace"
          :distance="distanceFromUser(selectedPlace)"
          @close="selectedId = null"
        />

        <FeaturedRouteCard
          v-if="data.route"
          :route="data.route"
          :selected-stop-id="selectedStop?.id ?? null"
          :distance-to-stop="distanceFromUser(selectedStop ?? data.route.stops[0] ?? null)"
          :can-open="canOpenPoint"
          :completed-ids="completedIds"
          @select-stop="selectedId = $event"
          @open-stop="openStop"
        />
        <StateBlock
          v-else
          :loading="false"
          :error="null"
          empty
          empty-icon="route"
          empty-text="Опубликованных семейных маршрутов пока нет"
        />
      </div>
    </template>
  </div>
</template>
