<script setup>
import { computed, onMounted, ref } from 'vue'
import PriorityAlert from './components/PriorityAlert.vue'
import StatusFilters from './components/StatusFilters.vue'
import TacticalMap from './components/TacticalMap.vue'
import TacticalMetrics from './components/TacticalMetrics.vue'
import ArchivalDossier from './components/ArchivalDossier.vue'
import ContributionModal from './components/ContributionModal.vue'
import AddLastStandModal from './components/AddLastStandModal.vue'
import { useAuthSession } from '@modules/auth'
import * as lastStandApi from './api.js'

const { session } = useAuthSession()

const uploadModalOpen = ref(false)
const addModalOpen = ref(false)

const points = ref([])
const selectedId = ref(null)
const statusFilter = ref(null)
const loadStatus = ref('idle') // idle | loading | loaded | error

// Роли, которым бэкенд разрешает добавлять новые точки.
const canAddPoint = computed(() =>
  ['searcher', 'local_historian', 'mentor', 'moderator'].includes(session.user?.role) ||
  session.user?.is_root,
)

const selectedPoint = computed(() => points.value.find((p) => p.id === selectedId.value) ?? null)

async function load() {
  loadStatus.value = 'loading'
  try {
    points.value = await lastStandApi.listLastStand({ status: statusFilter.value })
    if (!points.value.find((p) => p.id === selectedId.value)) {
      selectedId.value = points.value[0]?.id ?? null
    }
    loadStatus.value = 'loaded'
  } catch {
    loadStatus.value = 'error'
  }
}

function onFilterChange(status) {
  statusFilter.value = status
  load()
}

function onPointCreated(point) {
  points.value.unshift(point)
  selectedId.value = point.id
}

function onPointUpdated(point) {
  const i = points.value.findIndex((p) => p.id === point.id)
  if (i !== -1) points.value[i] = point
}

onMounted(load)
</script>

<template>
  <div class="flex flex-col w-full pb-16">
    <PriorityAlert />
    <StatusFilters :counts-source="points" @change="onFilterChange" />

    <div v-if="canAddPoint" class="flex justify-end mb-4 -mt-2">
      <button
        class="px-4 py-2 rounded-full bg-primary text-on-primary font-label-md text-label-md font-bold shadow-sm flex items-center gap-2"
        @click="addModalOpen = true"
      >
        <span class="material-symbols-outlined text-[18px]">add_location_alt</span>
        <span>Добавить точку «Последнего боя»</span>
      </button>
    </div>

    <section class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      <div class="lg:col-span-7 flex flex-col gap-4">
        <TacticalMap :points="points" :selected-id="selectedId" @select="selectedId = $event" />
        <TacticalMetrics :points="points" />
      </div>

      <div class="lg:col-span-5 flex flex-col gap-5">
        <p
          v-if="loadStatus === 'loaded' && !points.length"
          class="bg-surface-container-lowest rounded-lg p-6 shadow-sm text-on-surface-variant font-body-md text-body-md"
        >
          Пока нет точек с таким статусом.
          <span v-if="canAddPoint">Добавьте первую кнопкой выше.</span>
        </p>
        <ArchivalDossier
          v-else
          :point="selectedPoint"
          @open-upload="uploadModalOpen = true"
          @point-updated="onPointUpdated"
        />
      </div>
    </section>

    <ContributionModal v-model="uploadModalOpen" />
    <AddLastStandModal v-model="addModalOpen" @created="onPointCreated" />
  </div>
</template>
