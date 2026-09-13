<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { useAsync } from '@/core/async'
import StateBlock from '@/ui/StateBlock.vue'

import FeaturedRouteCard from './components/FeaturedRouteCard.vue'
import MemoryMap from './components/MemoryMap.vue'
import RouteFilters from './components/RouteFilters.vue'
import RoutesSearchBar from './components/RoutesSearchBar.vue'
import { fetchRoutesOverview } from './data'

const router = useRouter()
const { data, loading, error, retry } = useAsync(fetchRoutesOverview)

const query = ref('')
const activeFilters = ref<Set<string>>(new Set(['walking']))
const selectedPinId = ref<string | null>(null)

// Когда данные пришли — подсвечиваем начало маршрута дня, как в макете.
watch(data, (overview) => {
  if (overview && selectedPinId.value === null) selectedPinId.value = overview.featured.pinId
})

/** Точка маршрута — отдельный модуль. Нет его — кнопки старта просто не ведут никуда. */
const canOpenPoint = computed(() => router.hasRoute('route-point'))

function openStartPoint(): void {
  if (!data.value || !canOpenPoint.value) return
  void router.push({ name: 'route-point', params: { pointId: data.value.featured.startPointId } })
}
</script>

<template>
  <div class="relative flex w-full flex-col">
    <div class="z-30 flex flex-col gap-space-sm px-margin pb-space-sm pt-space-xs">
      <RoutesSearchBar v-model="query" />
      <RouteFilters v-if="data" v-model="activeFilters" :filters="data.filters" />
    </div>

    <div v-if="loading || error" class="px-margin">
      <StateBlock :loading="loading" :error="error" @retry="retry" />
    </div>

    <template v-else-if="data">
      <MemoryMap
        v-model:selected="selectedPinId"
        :pins="data.pins"
        :route-label="data.featured.mapLabel"
        :can-open-ar="canOpenPoint"
        @open-ar="openStartPoint"
      />
      <FeaturedRouteCard :route="data.featured" :can-start="canOpenPoint" @start="openStartPoint" />
    </template>
  </div>
</template>
