<script setup>
import { onMounted, ref, watch } from 'vue'
import { useAuthSession } from '@modules/auth'
import ExcursionMapModal from './ExcursionMapModal.vue'
import * as excursionsApi from '../api.js'

const { session } = useAuthSession()

const mapOpen = ref(false)
const selectedExcursion = ref(null)

function openMap(excursion) {
  selectedExcursion.value = excursion
  mapOpen.value = true
}

// core/models/excursion.py: ExcursionStatus
const STATUS_META = {
  scheduled: { label: 'Записаны', class: 'bg-secondary-container text-on-secondary-container' },
  gathering: { label: 'Идёт сбор группы', class: 'bg-tertiary-fixed text-on-tertiary-fixed' },
  finished: { label: 'Прошла', class: 'bg-secondary-fixed text-on-secondary-fixed' },
  cancelled: { label: 'Отменена', class: 'bg-error-container text-on-error-container' },
}

const joined = ref([])
const guiding = ref([])
const status = ref('idle') // idle | loading | loaded | error

async function load() {
  if (session.status !== 'authenticated') return
  status.value = 'loading'
  try {
    const mine = await excursionsApi.getMyExcursions(session.accessToken)
    joined.value = mine.joined
    guiding.value = mine.guiding
    status.value = 'loaded'
  } catch {
    status.value = 'error'
  }
}

onMounted(load)
watch(() => session.status, (s) => {
  if (s === 'authenticated') load()
})

function formatDate(iso) {
  return new Date(iso).toLocaleString('ru-RU', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div v-if="session.status === 'authenticated'" class="bg-surface-container-lowest rounded-lg p-6 shadow-sm flex flex-col gap-4">
    <div class="flex items-center gap-2.5">
      <span class="material-symbols-outlined text-primary text-[22px]">event_available</span>
      <div class="flex flex-col">
        <span class="font-headline-sm text-headline-sm text-on-surface">Мои экскурсии</span>
        <span class="font-body-sm text-body-sm text-on-surface-variant">search_hq_service, GET /excursions/mine</span>
      </div>
    </div>

    <p v-if="status === 'error'" class="font-body-sm text-body-sm text-error">
      Не удалось загрузить ваши экскурсии — search_hq_service недоступен
    </p>

    <template v-else-if="status === 'loaded'">
      <p v-if="!joined.length && !guiding.length" class="font-body-sm text-body-sm text-on-surface-variant">
        Вы пока не записаны ни на одну экскурсию.
      </p>

      <div v-if="joined.length" class="flex flex-col gap-2">
        <span class="font-label-sm text-label-sm text-on-surface-variant uppercase font-bold">Вы записаны</span>
        <button
          v-for="ex in joined"
          :key="ex.id"
          type="button"
          class="text-left bg-surface-container-low hover:bg-surface-container p-3.5 rounded-DEFAULT flex items-center justify-between gap-3 transition-colors"
          @click="openMap(ex)"
        >
          <div class="flex flex-col min-w-0">
            <span class="font-label-md text-label-md text-on-surface font-bold truncate">{{ ex.title }}</span>
            <span class="font-body-sm text-body-sm text-on-surface-variant truncate">
              {{ formatDate(ex.starts_at) }} · {{ ex.place_name || 'место уточняется' }}
            </span>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <span
              class="px-2.5 py-1 rounded-full font-label-sm text-label-sm font-bold"
              :class="STATUS_META[ex.status]?.class ?? 'bg-surface-container text-on-surface-variant'"
            >
              {{ STATUS_META[ex.status]?.label ?? ex.status }}
            </span>
            <span class="material-symbols-outlined text-[18px] text-on-surface-variant">map</span>
          </div>
        </button>
      </div>

      <div v-if="guiding.length" class="flex flex-col gap-2">
        <span class="font-label-sm text-label-sm text-on-surface-variant uppercase font-bold">Вы ведёте как гид</span>
        <button
          v-for="ex in guiding"
          :key="ex.id"
          type="button"
          class="text-left bg-surface-container-low hover:bg-surface-container p-3.5 rounded-DEFAULT flex items-center justify-between gap-3 transition-colors"
          @click="openMap(ex)"
        >
          <div class="flex flex-col min-w-0">
            <span class="font-label-md text-label-md text-on-surface font-bold truncate">{{ ex.title }}</span>
            <span class="font-body-sm text-body-sm text-on-surface-variant truncate">
              {{ formatDate(ex.starts_at) }} · {{ ex.registered_count }} записалось
            </span>
          </div>
          <span class="material-symbols-outlined text-[18px] text-on-surface-variant shrink-0">map</span>
        </button>
      </div>
    </template>

    <ExcursionMapModal v-model="mapOpen" :excursion="selectedExcursion" />
  </div>
</template>
