<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import { formatDistance } from '@/core/geo'
import MsIcon from '@/ui/MsIcon.vue'

import type { FamilyRoute, RoutePrompts } from '../data'

/**
 * Что на маршруте можно сделать по дороге — две интеграции из ТЗ:
 *
 * - рядом с точкой лежит неподтверждённая заметка народного архива, и её
 *   просят помочь проверить (п. 6);
 * - у точки нет «живого фото», и его предлагают создать для бойца из этого
 *   захоронения (п. 7).
 *
 * Подсказки считает `route_service`; экран только сводит их с точками маршрута,
 * чтобы человек понимал, где именно это по пути.
 */
const props = defineProps<{
  route: FamilyRoute
  prompts: RoutePrompts
}>()

const router = useRouter()

/** Точка маршрута по id — из неё берём номер шага и координаты для «рядом». */
const stops = computed(() => new Map(props.route.stops.map((stop) => [stop.id, stop])))

const archive = computed(() =>
  props.prompts.archive
    .map((prompt) => ({ prompt, stop: stops.value.get(prompt.waypoint_id) }))
    .filter((item): item is { prompt: (typeof props.prompts.archive)[number]; stop: FamilyRoute['stops'][number] } => !!item.stop),
)

const media = computed(() =>
  props.prompts.media
    .map((prompt) => ({ prompt, stop: stops.value.get(prompt.waypoint_id) }))
    .filter((item): item is { prompt: (typeof props.prompts.media)[number]; stop: FamilyRoute['stops'][number] } => !!item.stop),
)

/** Точек без «живого фото» обычно все сразу — сводим их в одну строку, а не в четыре карточки. */
const mediaPoints = computed(() => media.value.map(({ prompt, stop }) => `${stop.step}. ${prompt.title}`).join(', '))

const nothing = computed(() => archive.value.length === 0 && media.value.length === 0)

/** «Помочь проверить» — на экран архива, уже с точкой: там найдутся записи рядом. */
function openCheck(lat: number, lon: number): void {
  void router.push({ name: 'memory', query: { tab: 'archive', near: `${lat},${lon}` } })
}

/** «Оживить фото» — на экран «Живой памяти» с открытой формой заявки. */
function openClip(): void {
  void router.push({ name: 'memory', query: { tab: 'photo', clip: '1' } })
}
</script>

<template>
  <section v-if="!nothing" class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
    <div>
      <p class="font-archival text-archival uppercase text-on-surface-variant">По дороге</p>
      <h2 class="font-headline-sm text-headline-sm text-on-surface">Что можно сделать на маршруте</h2>
    </div>

    <article v-for="{ prompt, stop } in archive" :key="prompt.entry_id" class="flex items-start gap-space-sm">
      <span
        class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-tertiary-fixed text-on-tertiary-fixed"
        aria-hidden="true"
      >
        <MsIcon name="fact_check" :size="18" />
      </span>
      <div class="min-w-0 flex-1">
        <p class="font-label-md text-label-md text-on-surface">Помогите проверить: {{ prompt.title }}</p>
        <p class="font-body-sm text-body-sm text-on-surface-variant">
          Точка {{ stop.step }} · {{ stop.title }} · {{ formatDistance(prompt.distance_km) }} от неё
        </p>
        <button
          type="button"
          class="mt-space-xs flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-1.5 font-label-md text-label-md text-on-surface active:scale-95"
          @click="openCheck(stop.lat, stop.lon)"
        >
          <MsIcon name="travel_explore" :size="18" />
          Посмотреть записи рядом
        </button>
      </div>
    </article>

    <article v-if="media.length" class="flex items-start gap-space-sm">
      <span
        class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container"
        aria-hidden="true"
      >
        <MsIcon name="auto_awesome" :size="18" />
      </span>
      <div class="min-w-0 flex-1">
        <p class="font-label-md text-label-md text-on-surface">
          {{ media.length === 1 ? 'У этой точки нет «живого фото»' : 'У этих точек нет «живого фото»' }}
        </p>
        <p class="font-body-sm text-body-sm text-on-surface-variant">{{ mediaPoints }}</p>
        <button
          type="button"
          class="mt-space-xs flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-1.5 font-label-md text-label-md text-on-surface active:scale-95"
          @click="openClip"
        >
          <MsIcon name="add_a_photo" :size="18" />
          Оживить фото бойца
        </button>
      </div>
    </article>
  </section>
</template>
