<script setup lang="ts">
import { computed } from 'vue'

import { formatNumber, plural } from '@/core/format'
import MsIcon from '@/ui/MsIcon.vue'

import type { FamilyRoute, RouteStop } from '../data'

const props = defineProps<{
  route: FamilyRoute
  selectedStopId: string | null
  /** Сколько идти до точки, о которой рассказывает карточка, — если известно, где человек. */
  distanceToStop: string | null
  canOpen: boolean
  /** Пройденные точки — из прогресса `route_service`. `null` — прогресса нет (демо или маршрут не начат). */
  completedIds: string[] | null
}>()

const emit = defineEmits<{
  'select-stop': [id: string]
  'open-stop': [stop: RouteStop]
}>()

/** Точка, о которой сейчас карточка: выбранная на карте, а если ничего не выбрано — первая. */
const focusStop = computed(() => props.route.stops.find((stop) => stop.id === props.selectedStopId) ?? props.route.stops[0] ?? null)

const doneCount = computed(() => props.route.stops.filter((stop) => props.completedIds?.includes(stop.id)).length)

const stopsLabel = computed(() => `${props.route.stops.length} ${plural(props.route.stops.length, ['точка', 'точки', 'точек'])}`)
</script>

<template>
  <div class="flex w-full flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
    <div class="flex items-center gap-1.5 self-start rounded-full bg-tertiary-fixed px-2.5 py-1 text-on-tertiary-fixed-variant">
      <MsIcon name="auto_awesome" :size="15" filled class="text-tertiary" />
      <span class="font-archival text-archival uppercase">Семейный квест дня</span>
    </div>

    <div>
      <h2 class="ribbon-shimmer font-headline-md text-headline-md text-on-surface [--shimmer-base:theme(colors.ink.DEFAULT)]">
        {{ route.title }}
      </h2>
      <p class="mt-0.5 font-body-sm text-body-sm text-outline">{{ route.description }}</p>
    </div>

    <div class="flex flex-wrap items-center gap-space-xs">
      <span class="inline-flex items-center gap-1 rounded-full bg-surface-container-low px-2.5 py-1 font-label-md text-label-md text-on-surface">
        <MsIcon name="directions_walk" :size="15" class="text-secondary" />
        {{ formatNumber(route.distanceKm) }} км
      </span>
      <span class="inline-flex items-center gap-1 rounded-full bg-surface-container-low px-2.5 py-1 font-label-md text-label-md text-on-surface">
        <MsIcon name="schedule" :size="15" class="text-outline" />
        ~{{ route.durationMinutes }} мин
      </span>
      <span class="inline-flex items-center gap-1 rounded-full bg-surface-container-low px-2.5 py-1 font-label-md text-label-md text-on-surface">
        <MsIcon name="flag" :size="15" class="text-outline" />
        {{ stopsLabel }}
      </span>
      <span
        class="inline-flex items-center gap-1 rounded-full bg-secondary-container px-2.5 py-1 font-label-md text-label-md font-bold text-on-secondary-container"
      >
        <MsIcon name="family_restroom" :size="14" />
        Для семьи
      </span>
      <span
        v-if="completedIds && doneCount > 0"
        class="inline-flex items-center gap-1 rounded-full bg-secondary px-2.5 py-1 font-label-md text-label-md text-on-secondary"
      >
        <MsIcon name="task_alt" :size="14" />
        Пройдено {{ doneCount }} из {{ route.stops.length }}
      </span>
    </div>

    <!-- Точки маршрута: нажатие подсвечивает точку на карте -->
    <ol class="flex flex-col gap-1">
      <li v-for="stop in route.stops" :key="stop.id">
        <button
          type="button"
          class="flex w-full items-center gap-space-sm rounded-2xl px-2 py-1.5 text-left transition-colors"
          :class="focusStop?.id === stop.id ? 'bg-secondary-container/60' : 'hover:bg-surface-container-low'"
          :aria-pressed="focusStop?.id === stop.id"
          @click="emit('select-stop', stop.id)"
        >
          <span
            class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full font-label-md text-label-md"
            :class="focusStop?.id === stop.id ? 'bg-secondary text-on-secondary' : 'bg-surface-container-high text-on-surface-variant'"
          >
            <MsIcon v-if="completedIds?.includes(stop.id)" name="check" :size="16" />
            <template v-else>{{ stop.step }}</template>
          </span>
          <span class="min-w-0 flex-1 truncate font-label-lg text-label-lg text-on-surface">{{ stop.title }}</span>
          <MsIcon v-if="stop.hasAr" name="view_in_ar" :size="18" class="shrink-0 text-tertiary" aria-label="Есть AR" />
        </button>
      </li>
    </ol>

    <div v-if="focusStop?.kidTask" class="flex items-start gap-space-sm rounded-2xl bg-quest p-space-sm">
      <div class="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-tertiary-fixed text-tertiary shadow-sm">
        <MsIcon name="extension" :size="22" />
      </div>
      <div class="min-w-0 flex-1">
        <p class="font-label-md text-label-md font-bold leading-snug text-on-tertiary-fixed-variant">
          Задание на точке {{ focusStop.step }}
        </p>
        <p class="mt-0.5 font-body-sm text-body-sm leading-relaxed text-on-surface-variant">{{ focusStop.kidTask }}</p>
      </div>
    </div>

    <button
      v-if="focusStop"
      type="button"
      class="mt-1 flex h-13 w-full items-center justify-center gap-space-sm rounded-xl bg-primary-container px-space-md font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-60 short:h-11"
      :disabled="!canOpen"
      @click="emit('open-stop', focusStop)"
    >
      <MsIcon name="navigation" :size="22" />
      <span>{{ focusStop.step === 1 ? 'Начать путешествие' : `Открыть точку ${focusStop.step}` }}</span>
      <span v-if="distanceToStop" class="font-label-md text-label-md opacity-80">· {{ distanceToStop }}</span>
    </button>
  </div>
</template>
