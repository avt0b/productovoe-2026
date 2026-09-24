<script setup>
import { onMounted, ref, watch } from 'vue'
import { useAuthSession } from '@modules/auth'
import { checkForNewAchievements, ACHIEVEMENT_TITLES } from '../achievements.js'

const { session } = useAuthSession()

// Иконка/подсказка — только для отображения здесь; названия и сама логика
// «что нового» — в achievements.js, общие для всех страниц, которые могут
// начислить ачивку (не только эта).
const ACHIEVEMENT_META = {
  first_route_completed: { hint: 'Пройдите маршрут до конца', icon: 'route', bg: 'bg-secondary', fg: 'text-on-secondary' },
  archive_helper: {
    hint: 'Подтвердите или предложите запись в «Живой памяти»',
    icon: 'auto_stories',
    bg: 'bg-tertiary',
    fg: 'text-on-tertiary',
  },
  trip_volunteer: { hint: 'Съездите с отрядом на выезд', icon: 'volunteer_activism', bg: 'bg-primary', fg: 'text-on-primary' },
  donor: {
    hint: 'Задонатьте на сбор отряда в «Штабе»',
    icon: 'favorite',
    bg: 'bg-secondary-fixed',
    fg: 'text-on-secondary-fixed',
  },
}
const ALL_CODES = Object.keys(ACHIEVEMENT_TITLES)

const achievements = ref([])
const status = ref('idle') // idle | loading | loaded | error

async function load() {
  if (session.status !== 'authenticated') return
  status.value = 'loading'
  try {
    achievements.value = await checkForNewAchievements(session.accessToken, session.user?.id)
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

function isEarned(code) {
  return achievements.value.some((a) => a.code === code)
}

function earnedAt(code) {
  return achievements.value.find((a) => a.code === code)?.earned_at
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

    <div v-else-if="status === 'loaded'" class="grid grid-cols-2 sm:grid-cols-4 gap-4">
      <div
        v-for="code in ALL_CODES"
        :key="code"
        class="relative bg-surface-container-low p-4 rounded-DEFAULT flex flex-col items-center text-center group hover:bg-surface-container transition-all overflow-visible"
      >
        <div
          class="relative w-14 h-14 rounded-full flex items-center justify-center mb-3 transition-transform"
          :class="
            isEarned(code)
              ? [ACHIEVEMENT_META[code].bg, ACHIEVEMENT_META[code].fg, 'shadow-md group-hover:scale-105']
              : 'bg-surface-container-high text-on-surface-variant'
          "
        >
          <span class="material-symbols-outlined text-[28px]" :class="{ 'opacity-50': !isEarned(code) }">
            {{ isEarned(code) ? ACHIEVEMENT_META[code].icon : 'lock' }}
          </span>
        </div>

        <span
          class="font-headline-sm text-[15px] font-bold leading-snug"
          :class="isEarned(code) ? 'text-on-surface' : 'text-on-surface-variant'"
        >
          {{ ACHIEVEMENT_TITLES[code] }}
        </span>

        <span
          v-if="isEarned(code)"
          class="font-body-sm text-[11px] text-on-surface-variant mt-2 bg-surface-container-lowest px-2 py-0.5 rounded-full"
        >
          {{ formatDate(earnedAt(code)) }}
        </span>
        <span v-else class="font-body-sm text-[11px] text-on-surface-variant mt-2 italic">
          {{ ACHIEVEMENT_META[code].hint }}
        </span>
      </div>
    </div>
  </div>
</template>
