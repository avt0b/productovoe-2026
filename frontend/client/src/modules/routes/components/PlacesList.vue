<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { distanceKm, formatDistance, type GeoTone, type LatLon } from '@/core/geo'
import { plural } from '@/core/format'
import MsIcon from '@/ui/MsIcon.vue'

import { PLACE_KINDS, type MapPlace } from '../data'

/**
 * Список найденных мест под картой.
 *
 * Карта отвечает на «где это», список — на «что вообще нашлось»: после поиска
 * по слову или по году метки могут оказаться за краем экрана, и без списка
 * человек видит пустую карту и решает, что ничего не найдено.
 */
const props = defineProps<{
  places: MapPlace[]
  selectedId: string | null
  /** Где человек, если он разрешил определять место. Знаем — сортируем по близости. */
  user: LatLon | null
}>()

defineEmits<{ select: [id: string] }>()

/** Сколько строк показываем сразу: список для беглого взгляда, а не для листания всей области. */
const PAGE = 6
const shown = ref(PAGE)

// Сменился набор мест (поиск, фильтр, год) — список снова короткий.
watch(
  () => props.places,
  () => (shown.value = PAGE),
)

const TONE_CLASS: Record<GeoTone, string> = {
  primary: 'bg-primary-fixed text-primary',
  secondary: 'bg-secondary-fixed text-secondary',
  tertiary: 'bg-tertiary-fixed text-tertiary',
  neutral: 'bg-surface-container-high text-on-surface-variant',
}

const rows = computed(() => {
  const items = props.places.map((place) => ({
    place,
    km: props.user ? distanceKm(props.user, place) : null,
  }))
  // Знаем, где человек, — ближние вперёд: на прогулке важно, до чего дойти сейчас.
  if (props.user) items.sort((a, b) => (a.km ?? 0) - (b.km ?? 0))
  return items
})

const visible = computed(() => rows.value.slice(0, shown.value))
const rest = computed(() => rows.value.length - visible.value.length)
</script>

<template>
  <section class="flex flex-col gap-space-xs">
    <h2 class="font-archival text-archival uppercase text-on-surface-variant">
      Найдено {{ places.length }} {{ plural(places.length, ['место', 'места', 'мест']) }}
    </h2>

    <ul class="flex flex-col gap-1">
      <li v-for="row in visible" :key="row.place.id">
        <button
          type="button"
          class="flex w-full items-center gap-space-sm rounded-2xl p-space-sm text-left transition-colors"
          :class="selectedId === row.place.id ? 'bg-secondary-container/60' : 'bg-surface-container-lowest shadow-document hover:bg-surface-container-low'"
          :aria-pressed="selectedId === row.place.id"
          @click="$emit('select', row.place.id)"
        >
          <span
            class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full"
            :class="TONE_CLASS[PLACE_KINDS[row.place.kind].tone]"
          >
            <MsIcon :name="PLACE_KINDS[row.place.kind].icon" :size="18" />
          </span>
          <span class="min-w-0 flex-1">
            <span class="block truncate font-label-lg text-label-lg text-on-surface">{{ row.place.title }}</span>
            <span class="block truncate font-body-sm text-body-sm text-on-surface-variant">
              {{ PLACE_KINDS[row.place.kind].title }}<template v-if="row.place.dateText"> · {{ row.place.dateText }}</template>
            </span>
          </span>
          <span
            v-if="row.km !== null"
            class="shrink-0 font-label-md text-label-md text-outline"
            >{{ formatDistance(row.km) }}</span
          >
        </button>
      </li>
    </ul>

    <button
      v-if="rest > 0"
      type="button"
      class="self-center rounded-full px-space-md py-1.5 font-label-md text-label-md text-primary underline underline-offset-2"
      @click="shown += PAGE"
    >
      Показать ещё {{ Math.min(rest, PAGE) }}
    </button>
  </section>
</template>
