<script setup lang="ts">
import { computed, ref } from 'vue'

import { distanceKm, formatDistance, type LatLon } from '@/core/geo'
import MsIcon from '@/ui/MsIcon.vue'
import StateBlock from '@/ui/StateBlock.vue'

import { STATUS_STYLE, type FindRecord, type FindStatus } from '../data'

/**
 * Реестр мест списком под картой. Метки на карте удобно смотреть, но
 * неудобно перебирать, а найти бойца или часть по имени картой нельзя вовсе.
 */
const props = defineProps<{
  records: FindRecord[]
  selectedId: string | null
  /** Где человек — тогда список идёт от ближних мест к дальним. */
  from: LatLon | null
}>()

const emit = defineEmits<{ select: [id: string] }>()

const query = ref('')

const DOT: Record<FindStatus, string> = {
  found: 'bg-primary',
  confirmed: 'bg-tertiary',
  raised: 'bg-secondary',
}

/** Без геолокации первыми — те, кому нужна проверка: ради них реестр и открывают. */
const STATUS_ORDER: Record<FindStatus, number> = { found: 0, confirmed: 1, raised: 2 }

const rows = computed(() => {
  const needle = query.value.trim().toLowerCase()
  const origin = props.from
  return props.records
    .filter((record) =>
      !needle ||
      [record.title, record.unit, record.source, record.evidence].some((field) => field.toLowerCase().includes(needle)),
    )
    .map((record) => ({ record, km: origin ? distanceKm(origin, record) : null }))
    .sort((a, b) =>
      a.km !== null && b.km !== null ? a.km - b.km : STATUS_ORDER[a.record.status] - STATUS_ORDER[b.record.status],
    )
})
</script>

<template>
  <section class="flex flex-col gap-space-sm">
    <div>
      <p class="font-archival text-archival uppercase text-on-surface-variant">Реестр</p>
      <h2 class="font-headline-md text-headline-md text-on-surface">Все места</h2>
    </div>

    <label class="flex items-center gap-space-sm border-b border-outline-variant py-2 transition-colors focus-within:border-primary">
      <MsIcon name="search" :size="18" class="text-on-surface-variant" />
      <span class="sr-only">Поиск по реестру</span>
      <input
        v-model="query"
        type="search"
        placeholder="Боец, часть, источник"
        class="w-full border-none bg-transparent font-body-md text-body-md text-on-surface outline-none placeholder:text-on-surface-variant focus-visible:ring-0"
      />
    </label>

    <StateBlock
      v-if="rows.length === 0"
      :loading="false"
      :error="null"
      empty
      empty-icon="search_off"
      :empty-text="query ? 'По запросу ничего не нашлось' : 'Под выбранные фильтры мест нет'"
    />

    <ul v-else class="flex flex-col gap-space-xs">
      <li v-for="{ record, km } in rows" :key="record.id">
        <button
          type="button"
          class="flex w-full items-center gap-space-sm rounded-2xl p-space-sm text-left transition-colors duration-200 active:scale-[0.99]"
          :class="record.id === selectedId ? 'bg-surface-container-lowest shadow-document' : 'hover:bg-surface-container-low'"
          :aria-current="record.id === selectedId ? 'true' : undefined"
          @click="emit('select', record.id)"
        >
          <span
            class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-surface-container-high text-on-surface-variant"
            aria-hidden="true"
          >
            <MsIcon :name="STATUS_STYLE[record.status].icon" :size="18" />
          </span>
          <span class="flex min-w-0 flex-1 flex-col">
            <span class="flex items-center gap-1.5">
              <span class="h-2 w-2 shrink-0 rounded-full" :class="DOT[record.status]" />
              <span class="truncate font-label-lg text-label-lg text-on-surface">{{ record.title }}</span>
            </span>
            <span class="truncate font-body-sm text-body-sm text-on-surface-variant">
              {{ [record.unit, record.period].filter(Boolean).join(' · ') }}
            </span>
          </span>
          <span v-if="km !== null" class="shrink-0 font-label-sm text-label-sm text-on-surface-variant">{{ formatDistance(km) }}</span>
        </button>
      </li>
    </ul>
  </section>
</template>
