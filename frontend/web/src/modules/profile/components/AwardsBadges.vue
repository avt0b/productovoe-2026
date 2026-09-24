<script setup>
import { onMounted, ref, watch } from 'vue'
import { useAuthSession } from '@modules/auth'
import * as profileApi from '../api.js'

const { session } = useAuthSession()

// Дублирует ACHIEVEMENT_TITLES в user_service/core/models/achievement.py —
// бэкенд отдаёт только code и earned_at, иконку и подпись рисует фронт.
const ACHIEVEMENT_META = {
  first_route_completed: { title: 'Первый маршрут пройден', icon: 'route', bg: 'bg-secondary', fg: 'text-on-secondary' },
  archive_helper: { title: 'Помощник архива', icon: 'auto_stories', bg: 'bg-tertiary', fg: 'text-on-tertiary' },
  trip_volunteer: { title: 'Доброволец', icon: 'volunteer_activism', bg: 'bg-primary', fg: 'text-on-primary' },
  donor: { title: 'Жертвователь', icon: 'favorite', bg: 'bg-secondary-fixed', fg: 'text-on-secondary-fixed' },
}

const achievements = ref([])
const status = ref('idle') // idle | loading | loaded | error

async function load() {
  if (session.status !== 'authenticated') return
  status.value = 'loading'
  try {
    achievements.value = await profileApi.getMyAchievements(session.accessToken)
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
  return new Date(iso).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })
}
</script>

<template>
  <div class="bg-surface-container-lowest p-6 rounded-2xl shadow-document flex flex-col">
    <div class="flex items-center gap-3 mb-6">
      <div class="w-10 h-10 rounded-full bg-tertiary-fixed text-on-tertiary-fixed flex items-center justify-center">
        <span class="material-symbols-outlined text-[20px]">military_tech</span>
      </div>
      <div class="flex flex-col">
        <h2 class="font-headline-sm text-headline-sm font-bold text-on-surface">Награды и полевые значки</h2>
        <span class="font-body-sm text-body-sm text-on-surface-variant">user_service, GET /achievements/me</span>
      </div>
    </div>

    <p v-if="session.status !== 'authenticated'" class="font-body-sm text-body-sm text-on-surface-variant">
      Войдите, чтобы увидеть свои значки.
    </p>
    <p v-else-if="status === 'error'" class="font-body-sm text-body-sm text-error">
      Не удалось загрузить значки — user_service недоступен
    </p>
    <p v-else-if="status === 'loaded' && !achievements.length" class="font-body-sm text-body-sm text-on-surface-variant">
      Пока ни одного значка — пройдите маршрут, помогите с архивом, съездите волонтёром или задонатьте отряду.
    </p>

    <div v-else-if="achievements.length" class="grid grid-cols-2 sm:grid-cols-4 gap-4">
      <div
        v-for="a in achievements"
        :key="a.code"
        class="bg-surface-container-low p-4 rounded-DEFAULT flex flex-col items-center text-center group hover:bg-surface-container transition-all"
      >
        <div
          class="w-14 h-14 rounded-full flex items-center justify-center mb-3 shadow-md group-hover:scale-105 transition-transform"
          :class="[ACHIEVEMENT_META[a.code]?.bg ?? 'bg-outline', ACHIEVEMENT_META[a.code]?.fg ?? 'text-on-surface']"
        >
          <span class="material-symbols-outlined text-[28px]">{{ ACHIEVEMENT_META[a.code]?.icon ?? 'workspace_premium' }}</span>
        </div>
        <span class="font-headline-sm text-[15px] font-bold text-on-surface leading-snug">
          {{ ACHIEVEMENT_META[a.code]?.title ?? a.code }}
        </span>
        <span class="font-body-sm text-[11px] text-on-surface-variant mt-2 bg-surface-container-lowest px-2 py-0.5 rounded-full">
          {{ formatDate(a.earned_at) }}
        </span>
      </div>
    </div>
  </div>
</template>
