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
import InlineNotice from '@/ui/InlineNotice.vue'
import StateBlock from '@/ui/StateBlock.vue'

import FeaturedRouteCard from './components/FeaturedRouteCard.vue'
import PlaceCard from './components/PlaceCard.vue'
import PlacesList from './components/PlacesList.vue'
import RouteFilters from './components/RouteFilters.vue'
import RoutesSearchBar from './components/RoutesSearchBar.vue'
import TimelineFilter from './components/TimelineFilter.vue'
import { PLACE_KINDS, TIMELINE_YEARS, fetchRoutesOverview, type RouteStop } from './data'

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
/** Выбранные годы хронологии. Пусто — вся война. */
const activeYears = ref<Set<number>>(new Set())
const selectedId = ref<string | null>(null)

const normalizedQuery = computed(() => query.value.trim().toLowerCase())

/** Поиск и фильтр по виду места — без года: по ним же считаем, что показывать на шкале. */
const matchedPlaces = computed(() =>
  (data.value?.places ?? []).filter(
    (place) =>
      (activeKinds.value.size === 0 || activeKinds.value.has(place.kind)) &&
      (!normalizedQuery.value || `${place.title} ${place.description}`.toLowerCase().includes(normalizedQuery.value)),
  ),
)

/** Сколько мест приходится на каждый год — с учётом поиска и вида места. */
const yearCounts = computed(() => {
  const counts = Object.fromEntries(TIMELINE_YEARS.map((year) => [year, 0])) as Record<number, number>
  for (const place of matchedPlaces.value) {
    if (place.year !== null && place.year in counts) counts[place.year] += 1
  }
  return counts
})

const visiblePlaces = computed(() =>
  // Год выбран — места без даты прячем: утверждать, что событие было в 1943-м,
  // когда в архивной записи года нет, нельзя.
  activeYears.value.size === 0
    ? matchedPlaces.value
    : matchedPlaces.value.filter((place) => place.year !== null && activeYears.value.has(place.year)),
)

/** Хоть что-то отфильтровано — значит, есть что сбросить. */
const hasFilters = computed(() => Boolean(normalizedQuery.value) || activeKinds.value.size > 0 || activeYears.value.size > 0)

function resetFilters(): void {
  query.value = ''
  activeKinds.value = new Set()
  activeYears.value = new Set()
}

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
      <TimelineFilter v-if="data?.places.length" v-model="activeYears" :counts="yearCounts" />
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
        class="h-[420px] w-full short:h-64"
        @locate="startLocating"
      />

      <div class="flex flex-col gap-space-md px-margin pt-space-md">
        <InlineNotice v-if="geoProblem" icon="location_off">{{ geoProblem }}</InlineNotice>

        <InlineNotice v-if="visiblePlaces.length === 0" icon="filter_alt_off">
          Под поиск и фильтры мест нет.
          <button v-if="hasFilters" type="button" class="underline underline-offset-2" @click="resetFilters">
            Показать все
          </button>
        </InlineNotice>

        <PlaceCard
          v-if="selectedPlace"
          :key="selectedPlace.id"
          :place="selectedPlace"
          :distance="distanceFromUser(selectedPlace)"
          @close="selectedId = null"
        />

        <!-- Список найденного: метки могут оказаться за краем карты, и без него кажется, что ничего не нашлось. -->
        <PlacesList
          v-if="visiblePlaces.length"
          :places="visiblePlaces"
          :selected-id="selectedId"
          :user="userPosition"
          @select="selectedId = $event"
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
