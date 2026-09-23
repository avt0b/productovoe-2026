<script setup lang="ts">
import { computed } from 'vue'

import { plural } from '@/core/format'
import MsIcon from '@/ui/MsIcon.vue'

import { tripDay, type Trip, type TripFilter } from '../data'

/**
 * Календарь «Выходных с поисковиком» — лента дат, как в прототипе кейса:
 * видно, на какие выходные что-то есть, и одним нажатием оставить один день.
 */
const props = defineProps<{
  trips: Trip[]
  /** Выезды, куда человек записан. `null` — неизвестно, тогда «Мои» не показываем. */
  mine: Set<string> | null
}>()

const selected = defineModel<TripFilter>({ required: true })

const days = computed(() => {
  const byDate = new Map<string, Trip[]>()
  for (const trip of props.trips) byDate.set(trip.starts_on, [...(byDate.get(trip.starts_on) ?? []), trip])
  return [...byDate.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, trips]) => ({
      date,
      count: trips.length,
      mine: props.mine ? trips.some((trip) => props.mine!.has(trip.id)) : false,
      ...tripDay(date),
    }))
})

const mineCount = computed(() => (props.mine ? props.trips.filter((trip) => props.mine!.has(trip.id)).length : 0))

function chipClass(active: boolean): string {
  return active
    ? 'bg-secondary text-on-secondary shadow-float'
    : 'bg-surface-container-lowest text-on-surface shadow-document hover:bg-surface-container-low'
}
</script>

<template>
  <div
    class="no-scrollbar -mx-margin flex snap-x gap-space-xs overflow-x-auto px-margin py-1"
    role="radiogroup"
    aria-label="Даты выездов"
  >
    <button
      type="button"
      role="radio"
      :aria-checked="selected === 'all'"
      class="flex w-16 shrink-0 snap-start flex-col items-center justify-center gap-0.5 rounded-2xl py-1.5 transition-colors duration-200 active:scale-95"
      :class="chipClass(selected === 'all')"
      @click="selected = 'all'"
    >
      <MsIcon name="calendar_month" :size="20" />
      <span class="font-label-sm text-label-sm">Все · {{ trips.length }}</span>
    </button>
    <button
      v-if="mineCount"
      type="button"
      role="radio"
      :aria-checked="selected === 'mine'"
      class="flex w-16 shrink-0 snap-start flex-col items-center justify-center gap-0.5 rounded-2xl py-1.5 transition-colors duration-200 active:scale-95"
      :class="chipClass(selected === 'mine')"
      @click="selected = 'mine'"
    >
      <MsIcon name="how_to_reg" :size="20" />
      <span class="font-label-sm text-label-sm">Мои · {{ mineCount }}</span>
    </button>
    <button
      v-for="day in days"
      :key="day.date"
      type="button"
      role="radio"
      :aria-checked="selected === day.date"
      :aria-label="`${day.long}: ${day.count} ${plural(day.count, ['выезд', 'выезда', 'выездов'])}${day.mine ? ', вы записаны' : ''}`"
      class="relative flex w-14 shrink-0 snap-start flex-col items-center rounded-2xl py-1.5 transition-colors duration-200 active:scale-95"
      :class="chipClass(selected === day.date)"
      @click="selected = selected === day.date ? 'all' : day.date"
    >
      <span class="font-label-sm text-label-sm uppercase opacity-80">{{ day.weekday }}</span>
      <span class="font-headline-sm text-headline-sm">{{ day.day }}</span>
      <span class="font-label-sm text-label-sm opacity-80">{{ day.month }}</span>
      <span
        v-if="day.mine"
        class="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container ring-2 ring-surface"
        aria-hidden="true"
      >
        <MsIcon name="check" :size="15" />
      </span>
    </button>
  </div>
</template>
