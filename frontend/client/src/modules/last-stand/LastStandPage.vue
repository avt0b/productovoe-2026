<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { useAsync } from '@/core/async'
import MsIcon from '@/ui/MsIcon.vue'
import StateBlock from '@/ui/StateBlock.vue'

import RecordCard from './components/RecordCard.vue'
import SectorMap from './components/SectorMap.vue'
import StatusFilters from './components/StatusFilters.vue'
import { fetchLastStand, type FindStatus } from './data'

const { data, loading, error, retry } = useAsync(fetchLastStand)

/** Какие стадии находок показывать на карте. По умолчанию — все. */
const visibleStatuses = ref<Set<FindStatus>>(new Set(['found', 'confirmed', 'raised']))
const selectedPinId = ref<string | null>(null)

const visiblePins = computed(() => (data.value?.pins ?? []).filter((pin) => visibleStatuses.value.has(pin.status)))

// Как в макете: открыта карточка подтверждённой находки. Если выбранную метку
// скрыли фильтром — переключаемся на первую видимую, а не держим пустую карточку.
watch(
  visiblePins,
  (pins) => {
    if (pins.some((pin) => pin.id === selectedPinId.value)) return
    selectedPinId.value = (pins.find((pin) => pin.status === 'confirmed') ?? pins[0])?.id ?? null
  },
  { immediate: true },
)

const selectedRecord = computed(() => {
  const pin = data.value?.pins.find((item) => item.id === selectedPinId.value)
  return pin ? data.value?.records[pin.recordId] ?? null : null
})
</script>

<template>
  <div class="flex w-full flex-col space-y-space-md px-margin">
    <StateBlock v-if="loading || error" :loading="loading" :error="error" @retry="retry" />

    <template v-else-if="data">
      <div class="flex items-start gap-space-sm rounded-lg bg-primary-fixed/40 p-space-md shadow-sm">
        <div class="flex h-10 w-10 shrink-0 animate-pulse items-center justify-center rounded-full bg-primary text-on-primary shadow-sm">
          <MsIcon name="radar" :size="22" />
        </div>
        <div class="min-w-0 flex-1">
          <div class="flex items-center justify-between">
            <h2 class="font-headline-sm text-headline-sm leading-tight text-on-primary-fixed">{{ data.alert.title }}</h2>
            <span class="font-label-sm text-label-sm uppercase tracking-wider text-primary">{{ data.alert.distance }}</span>
          </div>
          <p class="mt-1 font-body-sm text-body-sm leading-snug text-on-surface-variant">{{ data.alert.text }}</p>
        </div>
      </div>

      <StatusFilters v-model="visibleStatuses" />

      <SectorMap v-model:selected="selectedPinId" :pins="visiblePins" :sector="data.sector" />

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
