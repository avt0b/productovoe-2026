<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { useAsync } from '@/core/async'
import { getMyProgress } from '@/core/services/routes'
import { can, useSessionStore } from '@/core/session'
import {
  distanceKm,
  formatDistance,
  geolocationProblem,
  useGeolocation,
  type GeoMarker,
  type GeoPath,
  type LatLon,
} from '@/core/geo'
import { HelpButton } from '@/features/onboarding'
import { PointSheet, usePointRoute } from '@/features/point-route'
import DemoDataBadge from '@/ui/DemoDataBadge.vue'
import MsIcon from '@/ui/MsIcon.vue'
import GeoMap from '@/ui/geo/GeoMap.vue'
import InlineNotice from '@/ui/InlineNotice.vue'
import StateBlock from '@/ui/StateBlock.vue'

import AddPlaceSheet from './components/AddPlaceSheet.vue'
import FeaturedRouteCard from './components/FeaturedRouteCard.vue'
import RoutePromptsCard from './components/RoutePromptsCard.vue'
import PlaceCard from './components/PlaceCard.vue'
import PlacesList from './components/PlacesList.vue'
import RouteFilters from './components/RouteFilters.vue'
import RoutesSearchBar from './components/RoutesSearchBar.vue'
import TimelineFilter from './components/TimelineFilter.vue'
import { PLACE_KINDS, TIMELINE_YEARS, fetchRoutesOverview, type MapPlace, type RouteStop } from './data'

const router = useRouter()
const session = useSessionStore()
const { data, loading, error, retry } = useAsync(fetchRoutesOverview)

/** Краевед ведёт свои маршруты — вход в редактор виден только ему (`AUTHOR_ROLES` в route_service). */
const canAuthor = computed(() => session.hasAccount && can.authorRoute(session.user))
/** Дополнять слой «ВОВ» могут ещё и поисковики (`_CONTRIBUTOR_ROLES` в map_service). */
const canAddPlace = computed(() => session.hasAccount && can.addPoi(session.user))
const addingPlace = ref(false)
/** Правит и убирает точку её автор или администратор — так же, как решает сервис. */
const editedPlace = ref<MapPlace | null>(null)

function canEditPlace(place: MapPlace): boolean {
  if (!session.hasAccount || data.value?.source === 'demo') return false
  return can.moderate(session.user) || place.createdBy === session.user?.id
}

/** Точку убрали — карточку закрываем: показывать нечего. */
async function placeRemoved(): Promise<void> {
  selectedId.value = null
  await retry()
}

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

/** Маршрут от человека до выбранной точки — один на карту. */
const pointRoute = usePointRoute({ position: userPosition, status: geoStatus, start: startLocating })
const { path: routePath, focus: routeFocus, state: routeState } = pointRoute

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

/** Маршрут дня пунктиром — «след» из кейса. Поверх — путь от человека до выбранной точки. */
const paths = computed<GeoPath[]>(() => {
  const route = data.value?.route
  const list: GeoPath[] = route ? [{ id: route.id, points: route.stops, tone: 'secondary', dashed: true }] : []
  if (routePath.value) list.push(routePath.value)
  return list
})

const selectedPlace = computed(() => data.value?.places.find((place) => place.id === selectedId.value) ?? null)
const selectedStop = computed(() => stops.value.find((stop) => stop.id === selectedId.value) ?? null)

// Как в макете: сначала подсвечено начало маршрута дня.
watch(data, (overview) => {
  if (overview?.route && selectedId.value === null) selectedId.value = overview.route.stops[0]?.id ?? null
})

// Выбранное место спрятали поиском или фильтром — закрываем его карточку.
// Спрятали то, куда ведёт маршрут, — маршрут тоже заканчиваем: вести некуда.
watch(markers, (items) => {
  if (selectedId.value && !items.some((marker) => marker.id === selectedId.value)) selectedId.value = null
  const routed = pointRoute.target.value
  if (routed && !items.some((marker) => marker.id === routed.id)) pointRoute.stop()
})

/** Карточка внизу раскрытой карты: место слоя «ВОВ» или точка маршрута дня. */
const sheetPoint = computed(() => {
  const place = selectedPlace.value
  if (place) {
    const facts = [
      place.dateText ? { icon: 'event', text: place.dateText } : null,
      place.source ? { icon: 'menu_book', text: place.source } : null,
    ].filter((fact) => fact !== null)
    return {
      point: { id: place.id, lat: place.lat, lon: place.lon },
      kicker: PLACE_KINDS[place.kind].title,
      icon: PLACE_KINDS[place.kind].icon,
      title: place.title,
      description: place.description,
      facts,
    }
  }
  const stop = selectedStop.value
  const route = data.value?.route
  if (stop && route) {
    return {
      point: { id: stop.id, lat: stop.lat, lon: stop.lon },
      kicker: `Точка ${stop.step} · ${route.title}`,
      icon: 'flag',
      title: stop.title,
      description: stop.kidTask ? `Задание: ${stop.kidTask}` : '',
      facts: stop.hasAr ? [{ icon: 'view_in_ar', text: 'Есть AR-точка' }] : [],
    }
  }
  return null
})

/**
 * Закрыли карточку. Пока маршрут ведёт к другой точке, возвращаемся к ней —
 * иначе управлять маршрутом было бы неоткуда. Закрыли карточку той точки,
 * куда ведём, — маршрут закончен.
 */
function closeSheet(): void {
  const routed = pointRoute.target.value
  if (routed && routed.id !== selectedId.value) {
    selectedId.value = routed.id
    return
  }
  pointRoute.stop()
  selectedId.value = null
}

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
      <div class="flex items-center gap-space-xs">
        <RoutesSearchBar v-model="query" class="min-w-0 flex-1" />
        <HelpButton />
      </div>
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
        :focus="routeFocus"
        :follow="routeState === 'active'"
        cluster
        expandable
        expand-on-select
        class="h-[420px] w-full short:h-64"
        @locate="startLocating"
      >
        <template v-if="sheetPoint" #sheet>
          <PointSheet
            :key="sheetPoint.point.id"
            :point="sheetPoint.point"
            :routing="pointRoute"
            :kicker="sheetPoint.kicker"
            :icon="sheetPoint.icon"
            :title="sheetPoint.title"
            :description="sheetPoint.description"
            :facts="sheetPoint.facts"
            @close="closeSheet"
          >
            <button
              v-if="selectedStop && canOpenPoint"
              type="button"
              class="flex h-11 items-center justify-center gap-space-xs rounded-full border border-white/20 bg-white/10 font-label-lg text-label-lg text-white transition-colors hover:bg-white/20 active:scale-[0.98]"
              @click="openStop(selectedStop)"
            >
              <MsIcon name="arrow_forward" :size="18" />
              Открыть точку маршрута
            </button>
            <button
              v-else-if="selectedPlace && canEditPlace(selectedPlace)"
              type="button"
              class="flex h-11 items-center justify-center gap-space-xs rounded-full border border-white/20 bg-white/10 font-label-lg text-label-lg text-white transition-colors hover:bg-white/20 active:scale-[0.98]"
              @click="editedPlace = selectedPlace"
            >
              <MsIcon name="edit" :size="18" />
              Поправить место
            </button>
          </PointSheet>
        </template>
      </GeoMap>

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
          :can-edit="canEditPlace(selectedPlace)"
          @close="selectedId = null"
          @edit="editedPlace = selectedPlace"
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
        <RoutePromptsCard v-if="data.route" :route="data.route" :prompts="data.prompts" />
        <StateBlock
          v-else
          :loading="false"
          :error="null"
          empty
          empty-icon="route"
          empty-text="Опубликованных семейных маршрутов пока нет"
        />

        <!-- Краеведу — его собственные маршруты: черновики и опубликованные. -->
        <RouterLink
          v-if="canAuthor"
          :to="{ name: 'my-routes' }"
          class="flex items-center gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document active:scale-[0.99]"
        >
          <span
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container"
            aria-hidden="true"
          >
            <MsIcon name="edit_note" :size="20" />
          </span>
          <span class="min-w-0 flex-1">
            <span class="block font-archival text-archival uppercase text-on-surface-variant">Краеведу</span>
            <span class="block font-headline-sm text-headline-sm text-on-surface">Мои маршруты</span>
            <span class="block font-body-sm text-body-sm text-on-surface-variant">Черновики, точки и публикация</span>
          </span>
          <MsIcon name="chevron_right" :size="20" class="shrink-0 text-on-surface-variant" />
        </RouterLink>

        <!-- «Дополнять данные» из ТЗ: памятника или окопа может не быть на карте. -->
        <button
          v-if="canAddPlace"
          type="button"
          class="flex items-center gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md text-left shadow-document active:scale-[0.99]"
          @click="addingPlace = true"
        >
          <span
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-tertiary-fixed text-on-tertiary-fixed"
            aria-hidden="true"
          >
            <MsIcon name="add_location_alt" :size="20" />
          </span>
          <span class="min-w-0 flex-1">
            <span class="block font-archival text-archival uppercase text-on-surface-variant">Слой «ВОВ»</span>
            <span class="block font-headline-sm text-headline-sm text-on-surface">Добавить место на карту</span>
            <span class="block font-body-sm text-body-sm text-on-surface-variant">Памятник, захоронение, окоп — со ссылкой на источник</span>
          </span>
          <MsIcon name="chevron_right" :size="20" class="shrink-0 text-on-surface-variant" />
        </button>
      </div>
    </template>

    <AddPlaceSheet v-if="addingPlace" @close="addingPlace = false" @created="retry" />
    <AddPlaceSheet
      v-else-if="editedPlace"
      :place="editedPlace"
      @close="editedPlace = null"
      @created="retry"
      @removed="placeRemoved"
    />
  </div>
</template>
