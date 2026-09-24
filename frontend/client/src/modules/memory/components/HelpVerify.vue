<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { errorText, plural } from '@/core/format'
import { distanceKm, formatDistance, geolocationProblem, useGeolocation, type LatLon } from '@/core/geo'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'

import { ENTRY_KINDS, fetchNearbyPending, type NearbyPending } from '../data'

/**
 * «Рядом есть неподтверждённая заметка — помогите проверить» из кейса.
 *
 * Центр поиска — точка маршрута, если с неё пришли (`point`), иначе место
 * человека. Геолокацию спрашиваем только по кнопке: окно разрешения при
 * открытии вкладки половина людей закрывает, не поняв зачем.
 */
const props = defineProps<{
  point: LatLon | null
  /** Краевед сам проверяет записи; остальные дополняют их тем, что знают. */
  canReview: boolean
}>()

const emit = defineEmits<{ help: [entry: NearbyPending]; review: [entryId: string] }>()

/** Радиус поиска: в пределах пешей прогулки от точки маршрута или соседних сёл. */
const RADIUS_KM = 10

const { position, status: geoStatus, start: locate } = useGeolocation()
const center = computed<LatLon | null>(() => props.point ?? position.value)
const geoProblem = computed(() => (props.point ? null : geolocationProblem(geoStatus.value)))

const entries = ref<NearbyPending[] | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

async function load(): Promise<void> {
  if (!center.value) return
  loading.value = true
  error.value = null
  try {
    entries.value = await fetchNearbyPending(center.value, RADIUS_KM)
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    loading.value = false
  }
}

// Первый фикс или новая точка маршрута — ищем заново; дрожание GPS в пару метров поиск не перезапускает.
watch(
  () => (center.value ? `${center.value.lat.toFixed(2)},${center.value.lon.toFixed(2)}` : null),
  (key) => key && void load(),
  { immediate: true },
)

const rows = computed(() =>
  (entries.value ?? [])
    .map((entry) => ({
      entry,
      km: center.value && entry.lat !== null && entry.lon !== null ? distanceKm(center.value, { lat: entry.lat, lon: entry.lon }) : null,
    }))
    .sort((a, b) => (a.km ?? Infinity) - (b.km ?? Infinity)),
)
</script>

<template>
  <section class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
    <div class="flex items-start gap-space-sm">
      <span
        class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-tertiary-fixed text-on-tertiary-fixed"
        aria-hidden="true"
      >
        <MsIcon name="travel_explore" :size="20" />
      </span>
      <div class="flex min-w-0 flex-1 flex-col gap-0.5">
        <p class="font-archival text-archival uppercase text-on-surface-variant">
          {{ point ? 'Рядом с точкой маршрута' : 'Рядом с вами' }}
        </p>
        <h2 class="font-headline-sm text-headline-sm text-on-surface">Помогите проверить</h2>
        <p class="font-body-sm text-body-sm text-on-surface-variant">
          {{
            canReview
              ? 'Записи в радиусе 10 км ждут вашего решения.'
              : 'Знаете, что было на этом месте, — расскажите: краевед решит быстрее.'
          }}
        </p>
      </div>
    </div>

    <button
      v-if="!center"
      type="button"
      class="flex items-center justify-center gap-space-xs self-start rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
      :disabled="geoStatus === 'locating'"
      @click="locate"
    >
      <MsIcon :name="geoStatus === 'locating' ? 'progress_activity' : 'my_location'" :size="18" :class="{ 'animate-spin': geoStatus === 'locating' }" />
      {{ geoStatus === 'locating' ? 'Определяем место…' : 'Найти записи рядом' }}
    </button>
    <InlineNotice v-if="geoProblem" tone="error" icon="location_off">{{ geoProblem }}</InlineNotice>

    <template v-if="center">
      <p v-if="loading && !entries" class="flex items-center gap-space-xs font-body-sm text-body-sm text-on-surface-variant" role="status">
        <MsIcon name="progress_activity" :size="18" class="animate-spin" />
        Ищем записи рядом…
      </p>
      <InlineNotice v-else-if="error" tone="error">
        {{ error }}
        <button type="button" class="ml-1 font-label-md text-label-md underline underline-offset-2" @click="load">Повторить</button>
      </InlineNotice>
      <p v-else-if="entries && !rows.length" class="flex items-center gap-space-xs font-body-sm text-body-sm text-on-surface-variant">
        <MsIcon name="task_alt" :size="18" class="text-secondary" />
        В радиусе 10 км всё проверено
      </p>
      <template v-else-if="rows.length">
        <p class="font-label-sm text-label-sm text-on-surface-variant">
          {{ rows.length }} {{ plural(rows.length, ['запись ждёт', 'записи ждут', 'записей ждут']) }} проверки
        </p>
        <ul class="flex flex-col divide-y divide-outline-variant/60">
          <li v-for="{ entry, km } in rows" :key="entry.id" class="flex items-center gap-space-sm py-2">
            <MsIcon :name="ENTRY_KINDS[entry.kind].icon" :size="18" class="shrink-0 text-on-surface-variant" />
            <div class="flex min-w-0 flex-1 flex-col">
              <span class="truncate font-label-md text-label-md text-on-surface">{{ entry.title }}</span>
              <span class="font-label-sm text-label-sm text-on-surface-variant">
                {{ [ENTRY_KINDS[entry.kind].title, km !== null ? formatDistance(km) : ''].filter(Boolean).join(' · ') }}
              </span>
            </div>
            <button
              type="button"
              class="shrink-0 rounded-full bg-surface-container-high px-space-sm py-1.5 font-label-md text-label-md text-on-surface active:scale-95"
              @click="canReview ? emit('review', entry.id) : emit('help', entry)"
            >
              {{ canReview ? 'Проверить' : 'Я знаю' }}
            </button>
          </li>
        </ul>
      </template>
    </template>
  </section>
</template>
