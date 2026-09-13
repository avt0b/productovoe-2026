<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { useAsync } from '@/core/async'
import { plural } from '@/core/format'
import { distanceKm, formatDistance, geolocationProblem, useGeolocation, type GeoMarker } from '@/core/geo'
import DemoDataBadge from '@/ui/DemoDataBadge.vue'
import GeoMap from '@/ui/geo/GeoMap.vue'
import MsIcon from '@/ui/MsIcon.vue'
import StateBlock from '@/ui/StateBlock.vue'

import RecordCard from './components/RecordCard.vue'
import StatusFilters from './components/StatusFilters.vue'
import { STATUS_STYLE, fetchLastStand, type FindStatus } from './data'

const { data, loading, error, retry } = useAsync(fetchLastStand)
const { position: userPosition, status: geoStatus, start: startLocating } = useGeolocation()

/** Какие стадии находок показывать на карте. По умолчанию — все. */
const visibleStatuses = ref<Set<FindStatus>>(new Set(['found', 'confirmed', 'raised']))
const selectedId = ref<string | null>(null)

const visibleRecords = computed(() => (data.value?.records ?? []).filter((record) => visibleStatuses.value.has(record.status)))

const markers = computed<GeoMarker[]>(() =>
  visibleRecords.value.map((record) => ({
    id: record.id,
    lat: record.lat,
    lon: record.lon,
    label: record.title,
    icon: STATUS_STYLE[record.status].icon,
    tone: STATUS_STYLE[record.status].tone,
  })),
)

// Сначала открыта точка, которой нужна помощь. Если выбранную метку скрыли
// фильтром — переключаемся на первую видимую, а не держим пустую карточку.
watch(
  visibleRecords,
  (records) => {
    if (records.some((record) => record.id === selectedId.value)) return
    selectedId.value = (records.find((record) => record.status === 'found') ?? records[0])?.id ?? null
  },
  { immediate: true },
)

const selectedRecord = computed(() => visibleRecords.value.find((record) => record.id === selectedId.value) ?? null)

/** Места, которым нужна проверка. */
const needHelp = computed(() => (data.value?.records ?? []).filter((record) => record.status === 'found'))

/** До ближайшего такого места — если известно, где человек. Это та самая строка «в 5 км от вас» из кейса. */
const nearestNeedKm = computed(() => {
  const user = userPosition.value
  if (!user || needHelp.value.length === 0) return null
  return Math.min(...needHelp.value.map((record) => distanceKm(user, record)))
})

const alertDistance = computed(() => (nearestNeedKm.value === null ? 'Орловская обл.' : `${formatDistance(nearestNeedKm.value)} от вас`))

const alertText = computed(() => {
  const count = needHelp.value.length
  if (count === 0) return 'Все отмеченные места проверены. Новые точки появятся здесь, как только их добавят поисковые отряды.'
  const places = plural(count, ['место гибели ждёт', 'места гибели ждут', 'мест гибели ждут'])
  return `${count} ${places} проверки. Помогите архивистам и поисковикам с верификацией.`
})

const geoProblem = computed(() => geolocationProblem(geoStatus.value))
</script>

<template>
  <div class="flex w-full flex-col space-y-space-md px-margin">
    <StateBlock v-if="loading || error" :loading="loading" :error="error" @retry="retry" />

    <template v-else-if="data">
      <DemoDataBadge v-if="data.source === 'demo'" />

      <div class="flex items-start gap-space-sm rounded-lg bg-primary-fixed/40 p-space-md shadow-sm">
        <div class="flex h-10 w-10 shrink-0 animate-pulse items-center justify-center rounded-full bg-primary text-on-primary shadow-sm">
          <MsIcon name="radar" :size="22" />
        </div>
        <div class="min-w-0 flex-1">
          <div class="flex items-center justify-between gap-space-xs">
            <h2 class="font-headline-sm text-headline-sm leading-tight text-on-primary-fixed">Внимание поисковика</h2>
            <span class="shrink-0 font-label-sm text-label-sm uppercase tracking-wider text-primary">{{ alertDistance }}</span>
          </div>
          <p class="mt-1 font-body-sm text-body-sm leading-snug text-on-surface-variant">{{ alertText }}</p>
        </div>
      </div>

      <StatusFilters v-model="visibleStatuses" />

      <GeoMap
        v-model:selected="selectedId"
        :markers="markers"
        :user="userPosition"
        :locating="geoStatus === 'locating'"
        label="Орловская область"
        class="h-80 w-full rounded-lg shadow-md"
        @locate="startLocating"
      />

      <p
        v-if="geoProblem"
        class="flex items-start gap-2 rounded-DEFAULT bg-surface-container-high px-3 py-2 font-body-sm text-body-sm text-on-surface-variant"
        role="status"
      >
        <MsIcon name="location_off" :size="18" class="mt-0.5 shrink-0" />
        {{ geoProblem }}
      </p>

      <RecordCard v-if="selectedRecord" :key="selectedRecord.id" :record="selectedRecord" />
      <StateBlock
        v-else
        :loading="false"
        :error="null"
        empty
        empty-icon="filter_alt_off"
        empty-text="Под выбранные фильтры находок нет"
      />
    </template>
  </div>
</template>
