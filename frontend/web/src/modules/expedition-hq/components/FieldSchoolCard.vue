<script setup>
import { computed, onMounted, ref } from 'vue'
import { useAuthSession } from '@modules/auth'
import { checkForNewAchievements } from '@modules/profile'
import * as hqApi from '../api.js'

const { session } = useAuthSession()

const trip = ref(null)
const squadName = ref('')
const loadStatus = ref('idle') // idle | loading | loaded | empty | error

// checklist хранится на бэкенде одной строкой (TripOut.checklist), делим на
// пункты сами; отметки "выполнено" — только локальный UX, у search_hq_service
// нет ручки для персонального прогресса по чек-листу.
const checklist = ref([])

const checkedCount = computed(() => checklist.value.filter((item) => item.checked).length)

const enrollState = ref('idle')
const enrollError = ref('')

async function load() {
  loadStatus.value = 'loading'
  try {
    const [trips, squads] = await Promise.all([hqApi.listUpcomingTrips(), hqApi.listSquads()])
    if (!trips.length) {
      loadStatus.value = 'empty'
      return
    }
    trip.value = trips[0]
    squadName.value = squads.find((s) => s.id === trip.value.squad_id)?.name ?? ''
    checklist.value = trip.value.checklist
      .split(/[,\n]/)
      .map((s) => s.trim())
      .filter(Boolean)
      .map((label) => ({ label, checked: false }))
    loadStatus.value = 'loaded'
  } catch {
    loadStatus.value = 'error'
  }
}

async function enroll() {
  if (enrollState.value !== 'idle' || !trip.value) return
  if (session.status !== 'authenticated') {
    enrollError.value = 'Войдите, чтобы записаться'
    return
  }
  enrollState.value = 'pending'
  enrollError.value = ''
  try {
    await hqApi.registerForTrip(session.accessToken, trip.value.id)
    enrollState.value = 'done'
    // trip_volunteer начисляется сразу при регистрации — салютуем тут же.
    checkForNewAchievements(session.accessToken, session.user?.id).catch(() => {})
  } catch (err) {
    enrollState.value = 'idle'
    enrollError.value = err.status === 409 ? 'Вы уже записаны на этот выезд' : (err.detail ?? 'Не удалось записаться')
  }
}

async function cancelEnroll() {
  if (enrollState.value !== 'done' || !trip.value) return
  enrollState.value = 'cancelling'
  enrollError.value = ''
  try {
    await hqApi.cancelRegistration(session.accessToken, trip.value.id)
    enrollState.value = 'idle'
  } catch (err) {
    enrollState.value = 'done'
    enrollError.value = err.detail ?? 'Не удалось отменить запись'
  }
}

onMounted(load)
</script>

<template>
  <div class="bg-secondary rounded-lg p-7 text-on-secondary shadow-lg relative overflow-hidden flex flex-col gap-6">
    <div class="absolute -right-20 -bottom-20 w-80 h-80 rounded-full bg-on-secondary-fixed/10 blur-2xl pointer-events-none" />

    <div class="flex items-center justify-between z-10">
      <div class="flex items-center gap-2 bg-secondary-fixed text-on-secondary-fixed px-3 py-1 rounded-full font-label-sm text-label-sm font-bold">
        <span class="material-symbols-outlined text-[16px]">school</span>
        <span>Полевая школа</span>
      </div>
      <span class="text-secondary-fixed-dim font-label-sm text-label-sm uppercase tracking-wider">search_hq_service</span>
    </div>

    <p v-if="loadStatus === 'empty'" class="font-body-md text-body-md text-secondary-fixed-dim z-10">
      Ближайших выездов пока не запланировано.
    </p>

    <template v-else-if="trip">
      <div class="flex flex-col gap-2 z-10">
        <h2 class="font-headline-lg text-headline-lg text-on-secondary font-extrabold leading-tight">
          {{ trip.title }}
        </h2>
        <p class="font-body-md text-body-md text-secondary-fixed-dim">{{ trip.description }}</p>
      </div>

      <div class="bg-on-secondary-fixed/30 rounded-DEFAULT p-4 flex flex-col gap-3 backdrop-blur-sm z-10">
        <div class="flex items-start gap-3">
          <span class="material-symbols-outlined text-tertiary-fixed text-[22px] shrink-0 mt-0.5">event</span>
          <div>
            <span class="font-label-lg text-label-lg text-on-secondary font-bold block">{{ trip.starts_on }}</span>
            <span class="font-body-sm text-body-sm text-secondary-fixed-dim">{{ trip.location }}</span>
          </div>
        </div>
        <div v-if="squadName" class="flex items-center gap-3 pt-2">
          <div class="w-10 h-10 rounded-full bg-secondary-fixed flex items-center justify-center text-on-secondary-fixed font-bold shrink-0">
            <span class="material-symbols-outlined text-[20px]">explore</span>
          </div>
          <div class="flex flex-col">
            <span class="font-label-md text-label-md text-on-secondary font-bold">{{ squadName }}</span>
            <span class="font-label-sm text-label-sm text-secondary-fixed-dim">Организатор выезда</span>
          </div>
        </div>
      </div>

      <div v-if="checklist.length" class="flex flex-col gap-3 z-10">
        <div class="flex items-center justify-between">
          <span class="font-label-lg text-label-lg text-on-secondary font-bold">Чек-лист новичка</span>
          <span class="font-label-sm text-label-sm text-tertiary-fixed font-bold">{{ checkedCount }} из {{ checklist.length }} готово</span>
        </div>
        <div class="flex flex-col gap-2.5">
          <label
            v-for="item in checklist"
            :key="item.label"
            class="flex items-center gap-3 p-2.5 rounded-DEFAULT bg-on-secondary-fixed/20 hover:bg-on-secondary-fixed/30 cursor-pointer transition-colors select-none"
          >
            <input v-model="item.checked" type="checkbox" class="w-5 h-5 rounded accent-tertiary-fixed cursor-pointer" />
            <span class="font-body-md text-body-md text-on-secondary flex-1">{{ item.label }}</span>
          </label>
        </div>
      </div>

      <div class="flex items-center justify-between p-3 rounded-DEFAULT bg-secondary-fixed/15 z-10">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-tertiary-fixed text-[18px]">groups</span>
          <span class="font-label-md text-label-md text-tertiary-fixed font-bold">Мест на выезде: {{ trip.capacity }}</span>
        </div>
        <span class="font-label-sm text-label-sm text-secondary-fixed-dim">Участие бесплатное</span>
      </div>

      <p v-if="enrollError" class="font-label-sm text-label-sm text-error-container z-10">{{ enrollError }}</p>

      <div class="flex flex-col gap-3 pt-2 z-10">
        <button
          class="w-full py-4 px-6 rounded-full font-label-lg text-label-lg font-bold shadow-md hover:scale-[0.99] transition-all flex items-center justify-center gap-2"
          :class="
            enrollState === 'done'
              ? 'bg-secondary-fixed text-on-secondary-fixed'
              : 'bg-tertiary-fixed hover:bg-tertiary-fixed-dim text-on-tertiary-fixed'
          "
          :disabled="enrollState === 'pending'"
          @click="enroll"
        >
          <span
            class="material-symbols-outlined text-[20px]"
            :class="{ 'animate-spin': enrollState === 'pending' }"
          >
            {{ enrollState === 'done' ? 'check_circle' : enrollState === 'pending' ? 'sync' : 'how_to_reg' }}
          </span>
          <span>
            {{
              enrollState === 'done'
                ? 'Вы в списке группы!'
                : enrollState === 'pending'
                  ? 'Заявка обрабатывается...'
                  : 'Записаться волонтером'
            }}
          </span>
        </button>
        <button
          v-if="enrollState === 'done' || enrollState === 'cancelling'"
          class="w-full py-2.5 px-6 rounded-full font-label-md text-label-md font-bold text-on-secondary hover:bg-on-secondary-fixed/15 transition-colors flex items-center justify-center gap-2"
          :disabled="enrollState === 'cancelling'"
          @click="cancelEnroll"
        >
          <span class="material-symbols-outlined text-[18px]" :class="{ 'animate-spin': enrollState === 'cancelling' }">
            {{ enrollState === 'cancelling' ? 'sync' : 'close' }}
          </span>
          <span>{{ enrollState === 'cancelling' ? 'Отменяем...' : 'Отменить запись' }}</span>
        </button>
      </div>
    </template>
  </div>
</template>
