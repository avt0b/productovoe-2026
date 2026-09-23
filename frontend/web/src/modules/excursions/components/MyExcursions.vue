<script setup>
import { onMounted, ref, watch } from 'vue'
import { useAuthSession } from '@modules/auth'
import ExcursionChecklistModal from './ExcursionChecklistModal.vue'
import ExcursionMapModal from './ExcursionMapModal.vue'
import GuideRatingModal from './GuideRatingModal.vue'
import * as excursionsApi from '../api.js'

const { session } = useAuthSession()

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
// accessToken, а не просто status: смена аккаунта (выйти → войти другим)
// меняет токен даже когда status остаётся 'authenticated' всё время.
watch(() => session.accessToken, load)

function formatDate(iso) {
  return new Date(iso).toLocaleString('ru-RU', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })
}

// Отписаться можно только пока экскурсия ещё не начала собираться
// (ExcursionService.cancel_registration: "После начала сбора отписаться нельзя").
const cancellingId = ref(null)
const cancelError = ref('')

async function cancelRegistration(ex) {
  cancellingId.value = ex.id
  cancelError.value = ''
  try {
    await excursionsApi.cancelRegistration(session.accessToken, ex.id)
    joined.value = joined.value.filter((j) => j.id !== ex.id)
  } catch (err) {
    cancelError.value = err.detail ?? 'Не удалось отписаться от экскурсии'
  } finally {
    cancellingId.value = null
  }
}

const checklistOpen = ref(false)
const checklistExcursion = ref(null)

function openChecklist(ex) {
  checklistExcursion.value = ex
  checklistOpen.value = true
}

const mapOpen = ref(false)
const mapExcursion = ref(null)

function openMap(ex) {
  mapExcursion.value = ex
  mapOpen.value = true
}

const ratingOpen = ref(false)
const ratingExcursion = ref(null)

function openRating(ex) {
  ratingExcursion.value = ex
  ratingOpen.value = true
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
      <p v-if="cancelError" class="font-body-sm text-body-sm text-error">{{ cancelError }}</p>
      <p v-if="!joined.length && !guiding.length" class="font-body-sm text-body-sm text-on-surface-variant">
        Вы пока не записаны ни на одну экскурсию.
      </p>

      <div v-if="joined.length" class="flex flex-col gap-2">
        <span class="font-label-sm text-label-sm text-on-surface-variant uppercase font-bold">Вы записаны</span>
        <div
          v-for="ex in joined"
          :key="ex.id"
          class="bg-surface-container-low p-3.5 rounded-DEFAULT flex flex-col sm:flex-row sm:items-center justify-between gap-3"
        >
          <div class="flex flex-col min-w-0">
            <span class="font-label-md text-label-md text-on-surface font-bold truncate">{{ ex.title }}</span>
            <span class="font-body-sm text-body-sm text-on-surface-variant truncate">
              {{ formatDate(ex.starts_at) }} · {{ ex.place_name || 'место уточняется' }}
            </span>
          </div>
          <div class="flex items-center gap-2 shrink-0 flex-wrap">
            <span
              class="px-2.5 py-1 rounded-full font-label-sm text-label-sm font-bold"
              :class="STATUS_META[ex.status]?.class ?? 'bg-surface-container text-on-surface-variant'"
            >
              {{ STATUS_META[ex.status]?.label ?? ex.status }}
            </span>
            <button
              type="button"
              class="px-3 py-1.5 rounded-full bg-surface-container text-on-surface font-label-sm text-label-sm font-bold flex items-center gap-1.5 hover:bg-surface-container-high transition-colors"
              @click="openMap(ex)"
            >
              <span class="material-symbols-outlined text-[16px]">map</span>
              Карта
            </button>
            <button
              type="button"
              class="px-3 py-1.5 rounded-full bg-surface-container text-on-surface font-label-sm text-label-sm font-bold flex items-center gap-1.5 hover:bg-surface-container-high transition-colors"
              @click="openChecklist(ex)"
            >
              <span class="material-symbols-outlined text-[16px]">checklist</span>
              Что взять
            </button>
            <button
              v-if="ex.status === 'finished' && ex.viewer?.checked_in_at"
              type="button"
              class="px-3 py-1.5 rounded-full bg-tertiary-container text-on-tertiary-container font-label-sm text-label-sm font-bold flex items-center gap-1.5 hover:opacity-90 transition-opacity"
              @click="openRating(ex)"
            >
              <span class="material-symbols-outlined text-[16px]">star</span>
              Оценить гида
            </button>
            <button
              v-if="ex.status === 'scheduled'"
              type="button"
              class="px-3 py-1.5 rounded-full bg-error-container text-on-error-container font-label-sm text-label-sm font-bold flex items-center gap-1.5 hover:opacity-90 transition-opacity disabled:opacity-50"
              :disabled="cancellingId === ex.id"
              @click="cancelRegistration(ex)"
            >
              <span class="material-symbols-outlined text-[16px]" :class="{ 'animate-spin': cancellingId === ex.id }">
                {{ cancellingId === ex.id ? 'sync' : 'close' }}
              </span>
              Отписаться
            </button>
          </div>
        </div>
      </div>

      <div v-if="guiding.length" class="flex flex-col gap-2">
        <span class="font-label-sm text-label-sm text-on-surface-variant uppercase font-bold">Вы ведёте как гид</span>
        <div
          v-for="ex in guiding"
          :key="ex.id"
          class="bg-surface-container-low p-3.5 rounded-DEFAULT flex items-center justify-between gap-3"
        >
          <div class="flex flex-col min-w-0">
            <span class="font-label-md text-label-md text-on-surface font-bold truncate">{{ ex.title }}</span>
            <span class="font-body-sm text-body-sm text-on-surface-variant truncate">
              {{ formatDate(ex.starts_at) }} · {{ ex.registered_count }} записалось
            </span>
          </div>
          <button
            type="button"
            class="px-3 py-1.5 rounded-full bg-surface-container text-on-surface font-label-sm text-label-sm font-bold flex items-center gap-1.5 hover:bg-surface-container-high transition-colors shrink-0"
            @click="openMap(ex)"
          >
            <span class="material-symbols-outlined text-[16px]">map</span>
            Карта
          </button>
        </div>
      </div>
    </template>

    <ExcursionChecklistModal v-model="checklistOpen" :excursion="checklistExcursion" />
    <ExcursionMapModal v-model="mapOpen" :excursion="mapExcursion" />
    <GuideRatingModal v-model="ratingOpen" :excursion="ratingExcursion" />
  </div>
</template>
